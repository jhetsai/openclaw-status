/*
 * PortfolioApplication - 蝦助攻客面板
 * 板子: Waveshare ESP32-S3-Touch-LCD-4B (480x480)
 *
 * 功能: 顯示持股總市值、天氣、現金、匯率
 * WiFi: 寫死 SSID/Password
 * 風格: Style C (High Contrast Dark)
 */

#ifndef MAIN_APPLICATION_PORTFOLIO_H_
#define MAIN_APPLICATION_PORTFOLIO_H_

#include <freertos/FreeRTOS.h>
#include <freertos/event_groups.h>
#include <esp_timer.h>
#include <esp_http_client.h>
#include <lvgl.h>

// WiFi 寫死設定
#define WIFI_SSID     "IoT"
#define WIFI_PASSWORD "057851463"

// JSON URL
#define PORTFOLIO_JSON_URL \
    "https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/assets/esp32_portfolio.json"
#define WEATHER_JSON_URL \
    "https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/tmp/weather.json"

// 顏色 (Style C: High Contrast Dark)
#define COLOR_BG         0x000000  // 純黑底
#define COLOR_CARD       0x1A1A2E  // 卡片背景
#define COLOR_CARD_LINE  0x3A3A5A  // 卡片邊框
#define COLOR_TEXT       0xFFFFFF  // 主文字白
#define COLOR_SUBTEXT    0x8888AA  // 次要文字灰紫
#define COLOR_POSITIVE   0x00E676  // 亮綠
#define COLOR_NEGATIVE   0xFF5252  // 警示紅
#define COLOR_MONEY      0xFFD54F  // 金色
#define COLOR_WIFI_OK    0x81C784  // 淺綠

class PortfolioApplication {
public:
    PortfolioApplication();
    ~PortfolioApplication();

    void Initialize();
    void Run();

private:
    // JSON fetch & parse
    void FetchPortfolio();
    void FetchWeather();
    esp_err_t DownloadJson(const char *url, char *buf, size_t len);
    void ParsePortfolioJson(const char *json);
    void ParseWeatherJson(const char *json);

    // LVGL screens
    enum class Screen { HOME, WEATHER, PORTFOLIO, CASH, FX };
    void SwitchScreen(Screen s);

    void CreateHomeScreen();
    void CreateWeatherScreen();
    void CreatePortfolioScreen();
    void CreateCashScreen();
    void CreateFxScreen();

    // UI helpers
    static lv_obj_t* CreateCard(lv_obj_t *parent, int y, int h);
    void CreateBackBtn(lv_obj_t *parent);
    static void HomeCardClickCallback(lv_event_t *e);
    static void BackBtnCallback(lv_event_t *e);

    // Update
    void UpdateHomeCards();

    // LVGL task
    static void LvglTask(void *arg);

    // Data structures
    struct Summary {
        float total_cost = 0, total_mktval = 0, total_gain = 0, total_gain_pct = 0;
    } summary_;

    struct Market {
        float cost = 0, mktval = 0, gain = 0, gain_pct = 0;
    } tw_, us_;

    struct Cash {
        float usd_amount = 0, usd_in_twd = 0, usd_rate = 0;
        float jpy_amount = 0, jpy_in_twd = 0, jpy_rate = 0;
    } cash_;

    struct Fx {
        float usd_twd = 0, jpy_twd = 0;
        char updated[32] = {0};
    } fx_;

    struct Weather {
        float temp = 0;
        float feels_like = 0;
        int weather_code = 0;
        char desc[64] = {0};
        int humidity = 0;
        char updated[32] = {0};
    } weather_;

    // LVGL objects
    lv_obj_t *home_scr_ = nullptr;
    lv_obj_t *home_wifi_lbl_ = nullptr;
    lv_obj_t *home_clock_lbl_ = nullptr;
    lv_obj_t *weather_scr_ = nullptr;
    lv_obj_t *portfolio_scr_ = nullptr;
    lv_obj_t *cash_scr_ = nullptr;
    lv_obj_t *fx_scr_ = nullptr;

    // Card label pointers (for UpdateHomeCards)
    lv_obj_t *lbl_temp_ = nullptr;
    lv_obj_t *lbl_weather_desc_ = nullptr;
    lv_obj_t *lbl_weather_humidity_ = nullptr;
    lv_obj_t *lbl_weather_updated_ = nullptr;
    lv_obj_t *lbl_portfolio_val_ = nullptr;
    lv_obj_t *lbl_portfolio_gain_ = nullptr;
    lv_obj_t *lbl_cash_ = nullptr;
    lv_obj_t *lbl_fx_ = nullptr;
    lv_obj_t *lbl_fx_usd_ = nullptr;
    lv_obj_t *lbl_cash_jpy_ = nullptr;
    lv_obj_t *lbl_cash_twd_ = nullptr;
    lv_obj_t *lbl_cash_jpy_twd_ = nullptr;
    lv_obj_t *lbl_solar_ = nullptr;

    // Current screen
    Screen current_screen_ = Screen::HOME;

    // Network state
    bool wifi_connected_ = false;
    bool wifi_just_connected_ = false;  // true after WiFi connects, cleared after first RSSI fetch
    bool sntp_needed_ = false;  // true after WiFi connects, triggers SNTP init in LvglTask
    time_t clock_base_time_ = 0;   // 對時後的基準時間
    time_t clock_seconds_ = 0;     // 硬體 timer 累加秒數（不受 NTP 跳動影響）
    char wifi_ssid_[32] = {0};
    int wifi_rssi_ = 0;
    bool ui_ready_ = false;
    bool clock_pending_ = false;  // clock timer tick pending
    float solar_kwh_ = 0;

    // LV task
    TaskHandle_t lvgl_task_h_ = nullptr;
    bool update_pending_ = false;

    // Timers
    esp_timer_handle_t clock_timer_ = nullptr;
    esp_timer_handle_t update_timer_ = nullptr;
};

#endif // MAIN_APPLICATION_PORTFOLIO_H_
