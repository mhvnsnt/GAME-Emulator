#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

typedef bool (*retro_environment_t)(unsigned, void *);
typedef void (*retro_video_refresh_t)(const void *, unsigned, unsigned, size_t);
typedef void (*retro_audio_sample_t)(int16_t, int16_t);
typedef size_t (*retro_audio_sample_batch_t)(const int16_t *, size_t);
typedef void (*retro_input_poll_t)(void);
typedef int16_t (*retro_input_state_t)(unsigned, unsigned, unsigned, unsigned);

typedef struct {
    const char *path;
    const void *data;
    size_t size;
    const char *meta;
} retro_game_info;

static retro_environment_t env_cb;
static retro_video_refresh_t video_cb;
static retro_audio_sample_t audio_cb;
static retro_audio_sample_batch_t audio_batch_cb;
static retro_input_poll_t input_poll_cb;
static retro_input_state_t input_state_cb;

void retro_set_environment(retro_environment_t cb) { env_cb = cb; }
void retro_set_video_refresh(retro_video_refresh_t cb) { video_cb = cb; }
void retro_set_audio_sample(retro_audio_sample_t cb) { audio_cb = cb; }
void retro_set_audio_sample_batch(retro_audio_sample_batch_t cb) { audio_batch_cb = cb; }
void retro_set_input_poll(retro_input_poll_t cb) { input_poll_cb = cb; }
void retro_set_input_state(retro_input_state_t cb) { input_state_cb = cb; }

void retro_init(void) {
    (void)env_cb;
    (void)audio_cb;
    (void)audio_batch_cb;
    (void)input_poll_cb;
    (void)input_state_cb;
}

bool retro_load_game(const retro_game_info *info) {
    return info != NULL && info->path != NULL;
}

void retro_run(void) {
    static const uint32_t pixel = 0xFF336699u;
    if (video_cb != NULL) {
        video_cb(&pixel, 1, 1, sizeof(pixel));
    }
}

void retro_unload_game(void) {}
void retro_deinit(void) {}
