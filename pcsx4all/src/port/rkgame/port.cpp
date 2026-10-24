// SPDX-License-Identifier: GPL-2.0-or-later
// Copyright (c) 2026 Jose Pilas and contributors.
// API integration follows PCSX4ALL's GPL SDL port; PCSX/PCSX-df/PCSX4ALL
// teams and Ryan Schultz retain upstream rights. No vendor implementation.
#include "port.h"
#include "r3000a.h"
#include "plugins.h"
#include "plugin_lib.h"
#include "misc.h"
#include "spu/spu_pcsxrearmed/spu_config.h"
#include "gpu/gpu_unai/gpu.h"
#include <algorithm>
#include <cerrno>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <limits.h>
#include <sstream>
#include <string>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

extern u32 cycle_multiplier;
unsigned short *SCREEN = nullptr;
char sstatesdir[PATH_MAX] = "/persist/states/pcsx4all";
namespace {
uint16_t fallback[320 * 240]{};
int frameWidth = 320, frameHeight = 240, framePitch = 320;
uint16_t pads[2] = {0xffff, 0xffff};
rkgame_pcsx_video_cb present = nullptr;
rkgame_pcsx_input_cb readPad = nullptr;
rkgame_pcsx_log_cb logger = nullptr;
std::string configDirectory = "/persist/config/pcsx4all";
int analogArrow = 0, analogMode = 0;
void report(const char *message) {
    if (logger) logger(message); else std::fputs(message, stderr);
}
template<size_t N> void assign(char (&destination)[N], const std::string &value) {
    std::snprintf(destination, N, "%s", value.c_str());
}
std::string environment(const char *key, const char *fallbackValue) {
    const char *value = std::getenv(key);
    return value && *value ? value : fallbackValue;
}
void defaults() {
    Config = {};
    configDirectory = environment("LILSMOKE_PCSX_CONFIG_ROOT", "/persist/config/pcsx4all");
    const auto saves = environment("LILSMOKE_PCSX_SAVE_ROOT", "/persist/saves/pcsx4all");
    const auto bios = environment("LILSMOKE_PCSX_BIOS_ROOT", "/persist/bios");
    assign(sstatesdir, environment("LILSMOKE_PCSX_LEGACY_STATE_ROOT", "/persist/states/pcsx4all"));
    for (const auto &path : {configDirectory, saves, bios, std::string(sstatesdir), configDirectory + "/patches"})
        if (mkdir(path.c_str(), 0777) && errno != EEXIST) report("PCSX: cannot create runtime directory\n");
    assign(Config.Mcd1, saves + "/mcd001.mcr"); assign(Config.Mcd2, saves + "/mcd002.mcr");
    assign(Config.BiosDir, bios); assign(Config.Bios, "scph1001.bin");
    assign(Config.PatchesDir, configDirectory + "/patches"); assign(Config.LastDir, configDirectory);
    struct stat info{};
    Config.HLE = stat((bios + "/scph1001.bin").c_str(), &info) || !S_ISREG(info.st_mode) || info.st_size != 524288;
    Config.PsxAuto = 1; Config.Cpu = CPU_DYNAREC;
    Config.SpuUpdateFreq = SPU_UPDATE_FREQ_16; Config.ForcedXAUpdates = FORCED_XA_UPDATES_AUTO;
    Config.ShowFps = 1; Config.FrameLimit = 1;
    analogArrow = analogMode = 0;
    spu_config.iHaveConfiguration = 1; spu_config.iVolume = 1024;
    spu_config.iXAPitch = 0; spu_config.iUseReverb = 0; spu_config.iUseInterpolation = 0;
    spu_config.iTempo = 1; spu_config.iUseThread = 0; spu_config.iUseFixedUpdates = 1; spu_config.iDisabled = 0;
    cycle_multiplier = 0x100;
    gpu_unai_config_ext.ilace_force = 0; gpu_unai_config_ext.pixel_skip = 0;
    gpu_unai_config_ext.lighting = 1; gpu_unai_config_ext.fast_lighting = 1;
    gpu_unai_config_ext.blending = 1; gpu_unai_config_ext.dithering = 0;
    pads[0] = pads[1] = 0xffff;
}
// The public CONFIG_VERSION 0 keys and compatibility aliases are data.
// This table-based implementation replaces the recovered parser control flow.
struct ByteSetting { const char *key; u8 PcsxConfig::*field; };
const ByteSetting byteSettings[] = {
    {"Xa", &PcsxConfig::Xa}, {"Mdec", &PcsxConfig::Mdec}, {"PsxAuto", &PcsxConfig::PsxAuto},
    {"Cdda", &PcsxConfig::Cdda}, {"HLE", &PcsxConfig::HLE}, {"SlowBoot", &PcsxConfig::SlowBoot},
    {"RCntFix", &PcsxConfig::RCntFix}, {"VSyncWA", &PcsxConfig::VSyncWA}, {"Cpu", &PcsxConfig::Cpu},
    {"PsxType", &PcsxConfig::PsxType}, {"SpuIrq", &PcsxConfig::SpuIrq}, {"SyncAudio", &PcsxConfig::SyncAudio},
    {"ShowFps", &PcsxConfig::ShowFps}, {"FrameLimit", &PcsxConfig::FrameLimit}
};
void setNumber(const std::string &key, int value) {
    for (const auto &setting : byteSettings)
        if (key == setting.key) { Config.*(setting.field) = static_cast<u8>(value); return; }
    if (key == "SpuUpdateFreq") Config.SpuUpdateFreq = value >= SPU_UPDATE_FREQ_MIN && value <= SPU_UPDATE_FREQ_MAX ? value : SPU_UPDATE_FREQ_DEFAULT;
    else if (key == "ForcedXAUpdates") Config.ForcedXAUpdates = value >= FORCED_XA_UPDATES_MIN && value <= FORCED_XA_UPDATES_MAX ? value : FORCED_XA_UPDATES_DEFAULT;
    else if (key == "FrameSkip") Config.FrameSkip = value >= FRAMESKIP_MIN && value <= FRAMESKIP_MAX ? value : FRAMESKIP_OFF;
    else if (key == "AnalogArrow") analogArrow = value;
    else if (key == "Analog_Mode") analogMode = value > 2 ? 0 : value;
    else if (key == "SpuUseInterpolation") spu_config.iUseInterpolation = value;
    else if (key == "SpuUseReverb") spu_config.iUseReverb = value;
    else if (key == "SpuVolume") spu_config.iVolume = std::clamp(value, 0, 1024);
    else if (key == "CycleMultiplier") cycle_multiplier = value;
    else if (key == "clip_368" || key == "pixel_skip") gpu_unai_config_ext.pixel_skip = value & 1;
    else if (key == "lighting") gpu_unai_config_ext.lighting = value & 1;
    else if (key == "fast_lighting") gpu_unai_config_ext.fast_lighting = value & 1;
    else if (key == "blending") gpu_unai_config_ext.blending = value & 1;
    else if (key == "dithering") gpu_unai_config_ext.dithering = value & 1;
    else if (key == "interlace") gpu_unai_config_ext.ilace_force = value & 7;
}
void compatibilitySettings() {
    const std::string title(CdromId);
    if (title == "SLPS02124") gpu_unai_config_ext.pixel_skip = 1;
    if (title == "SLPS03503") Config.VSyncWA = 1;
    if (title == "SCES01564" || title == "SCES02031") analogMode = 2;
    if (title == "SCPS45183") Config.RCntFix = 1;
    // The previous SLES00613/SLED00690 flag was never read and had no effect.
}
}
void config_load() {
    std::ifstream stream(configDirectory + "/pcsx4all.cfg");
    std::string line, key;
    int version = -1;
    if (!std::getline(stream, line)) return;
    std::istringstream header(line);
    if (!(header >> key >> version) || key != "CONFIG_VERSION" || version != CONFIG_VERSION) return;
    while (std::getline(stream, line)) {
        std::istringstream row(line);
        std::string value;
        if (!(row >> key)) continue;
        std::getline(row >> std::ws, value);
        if (!value.empty() && value.back() == '\r') value.pop_back();
        if (key == "LastDir") assign(Config.LastDir, value);
        else if (key == "BiosDir") assign(Config.BiosDir, value);
        else if (key == "Bios") assign(Config.Bios, value);
        else {
            char *end = nullptr;
            const long number = std::strtol(value.c_str(), &end, key == "CycleMultiplier" ? 16 : 10);
            if (end != value.c_str() && *end == '\0') setNumber(key, static_cast<int>(number));
        }
    }
}
void config_save() {
    std::ofstream stream(configDirectory + "/pcsx4all.cfg");
    stream << "CONFIG_VERSION " << CONFIG_VERSION << '\n';
    for (const auto &setting : byteSettings) stream << setting.key << ' ' << static_cast<int>(Config.*(setting.field)) << '\n';
    stream << "SpuUpdateFreq " << static_cast<int>(Config.SpuUpdateFreq)
           << "\nForcedXAUpdates " << static_cast<int>(Config.ForcedXAUpdates)
           << "\nFrameSkip " << static_cast<int>(Config.FrameSkip)
           << "\nAnalogArrow " << analogArrow << "\nAnalog_Mode " << analogMode
           << "\nSpuUseInterpolation " << spu_config.iUseInterpolation
           << "\nSpuUseReverb " << spu_config.iUseReverb << "\nSpuVolume " << spu_config.iVolume
           << "\nCycleMultiplier " << std::hex << cycle_multiplier << std::dec
           << "\ninterlace " << static_cast<int>(gpu_unai_config_ext.ilace_force)
           << "\nclip_368 " << static_cast<int>(gpu_unai_config_ext.pixel_skip)
           << "\nlighting " << static_cast<int>(gpu_unai_config_ext.lighting)
           << "\nfast_lighting " << static_cast<int>(gpu_unai_config_ext.fast_lighting)
           << "\nblending " << static_cast<int>(gpu_unai_config_ext.blending)
           << "\ndithering " << static_cast<int>(gpu_unai_config_ext.dithering)
           << "\nLastDir " << Config.LastDir << "\nBiosDir " << Config.BiosDir << "\nBios " << Config.Bios << '\n';
}
extern "C" int pcsx_load_game(const char **path) {
    defaults(); config_load();
    const char *disc = path && *path ? *path : "";
    SetIsoFile(disc);
    if (psxInit() < 0) { report("PCSX: CPU initialization failed\n"); return -1; }
    if (LoadPlugins() < 0) { psxShutdown(); report("PCSX: plugin initialization failed\n"); return -1; }
    if (!SCREEN) SCREEN = fallback;
    pl_init(); psxReset();
    int result = 0;
    if (*disc && (CheckCdrom() < 0 || LoadCdrom() < 0)) {
        report("PCSX: disc could not be loaded\n"); SetIsoFile(nullptr); result = -1;
    } else {
        compatibilitySettings();
        if (*disc || !Config.HLE) psxCpu->Execute();
    }
    config_save(); ReleasePlugins(); psxShutdown();
    return result;
}
extern "C" void rkgame_pcsx_set_video_buffer(uint16_t *pixels, int width, int height, int pitch) {
    if (pixels && width > 0 && height > 0 && pitch >= width) {
        SCREEN = pixels; frameWidth = width; frameHeight = height; framePitch = pitch;
    }
}
extern "C" void rkgame_pcsx_set_video_callback(rkgame_pcsx_video_cb callback) { present = callback; }
extern "C" void rkgame_pcsx_set_input_callback(rkgame_pcsx_input_cb callback) { readPad = callback; }
extern "C" void rkgame_pcsx_set_log_callback(rkgame_pcsx_log_cb callback) { logger = callback; }
// ABI compatibility only: paths no longer use a vendor-global work_path buffer.
extern "C" void rkgame_pcsx_set_work_path(const char *) {}
void pad_update() { if (readPad) for (int port = 0; port < 2; ++port) pads[port] = readPad(port); }
unsigned short pad_read(int port) { return pads[port == 0 ? 0 : 1]; }
void video_flip() { if (present) present(SCREEN ? SCREEN : fallback, frameWidth, frameHeight, framePitch); }
void video_clear() {
    uint16_t *pixels = SCREEN ? SCREEN : fallback;
    for (int row = 0; row < frameHeight; ++row) std::fill_n(pixels + row * framePitch, frameWidth, 0);
}
void port_printf(int, int, const char *) {}
unsigned get_ticks() {
    timespec now{}; clock_gettime(CLOCK_MONOTONIC, &now);
    return static_cast<unsigned>(now.tv_sec * 1000ULL + now.tv_nsec / 1000000);
}
void wait_ticks(unsigned milliseconds) {
    timespec pause{static_cast<time_t>(milliseconds / 1000), static_cast<long>(milliseconds % 1000) * 1000000};
    while (nanosleep(&pause, &pause) && errno == EINTR) {}
}
int SelectGame() { return 0; }
int GameMenu() { return 0; }
int state_load(int slot) {
    const auto file = std::string(sstatesdir) + "/" + CdromId + "." + std::to_string(slot) + ".sav";
    return FileExists(file.c_str()) ? LoadState(file.c_str()) : -1;
}
int state_save(int slot) {
    return SaveState((std::string(sstatesdir) + "/" + CdromId + "." + std::to_string(slot) + ".sav").c_str());
}
