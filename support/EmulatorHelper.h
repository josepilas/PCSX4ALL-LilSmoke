// Copyright (c) 2026 Jose Pilas and contributors.
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.
// SPDX-License-Identifier: MPL-2.0
#pragma once
#include <chrono>
#include <string>
#include <vector>
#include <cerrno>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <sys/wait.h>
#include <unistd.h>

namespace lilsmoke {
inline std::string readEmulatorHelper(const std::string &helper, const std::vector<std::string> &args,
                                      size_t maxBytes, unsigned seconds, bool quiet = true) {
    if (access(helper.c_str(), X_OK) != 0) return {};
    int fds[2];
    if (pipe(fds) != 0) return {};
    const pid_t child = fork();
    if (child == 0) {
        dup2(fds[1], STDOUT_FILENO);
        const int null = open("/dev/null", O_RDWR);
        if (null >= 0) { dup2(null, STDIN_FILENO); if (quiet) dup2(null, STDERR_FILENO); close(null); }
        close(fds[0]); close(fds[1]);
        std::vector<char *> argv{const_cast<char *>(helper.c_str())};
        for (const auto &arg : args) argv.push_back(const_cast<char *>(arg.c_str()));
        argv.push_back(nullptr);
        execv(helper.c_str(), argv.data());
        _exit(127);
    }
    close(fds[1]);
    if (child < 0) { close(fds[0]); return {}; }
    fcntl(fds[0], F_SETFL, O_NONBLOCK);
    std::string out;
    bool done = false, valid = true;
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(seconds);
    while (!done && std::chrono::steady_clock::now() < deadline) {
        pollfd fd{fds[0], POLLIN | POLLHUP, 0};
        poll(&fd, 1, 100);
        char buffer[4096];
        const ssize_t n = read(fds[0], buffer, sizeof(buffer));
        if (n > 0) {
            if (out.size() + static_cast<size_t>(n) > maxBytes) { valid = false; break; }
            out.append(buffer, static_cast<size_t>(n));
        } else if (n == 0) done = true;
        else if (errno != EINTR && errno != EAGAIN) { valid = false; break; }
    }
    close(fds[0]);
    if (!done || !valid) kill(child, SIGKILL);
    int status = 0;
    pid_t reaped = 0;
    while ((reaped = waitpid(child, &status, WNOHANG)) == 0 && std::chrono::steady_clock::now() < deadline)
        poll(nullptr, 0, 10);
    if (reaped != child) {
        valid = false;
        kill(child, SIGKILL);
        while (waitpid(child, &status, 0) < 0 && errno == EINTR) {}
    }
    return done && valid && WIFEXITED(status) && WEXITSTATUS(status) == 0 ? out : std::string();
}

}
