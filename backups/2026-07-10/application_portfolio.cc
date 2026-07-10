/*
 * PortfolioApplication - 蝦助攻客面板 實作
 * 架構：Initialize() 做輕量準備，UI 建立延後到 LvglTask (保證 LVGL 已在運行)
 */

#include "application_portfolio.h"
#include "board.h"
#include <ssid_manager.h>
#include <esp_log.h>
#include <esp_err.h>
#include <esp_timer.h>
#include <esp_lvgl_port.h>
#include <esp_wifi.h>
// Chinese fonts from 78__xiaozhi-fonts (pre-linked)
LV_FONT_DECLARE(font_puhui_16_4);
LV_FONT_DECLARE(font_puhui_20_4);

#include <esp_crt_bundle.h>
#include <esp_wifi.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include <esp_netif_sntp.h>

static const char *TAG = "PortfolioApp";

// Format number with thousands separators: 6333765 -> "6,333,765"
static void FormatWithCommas(char *buf, size_t len, double value) {
    char tmp[32];
    snprintf(tmp, sizeof(tmp), "%.0f", value);
    int src_len = strlen(tmp);
    int commas = (src_len > 0) ? (src_len - 1) / 3 : 0;
    if (commas <= 0) {
        snprintf(buf, len, "%s", tmp);
        return;
    }
    int out_len = src_len + commas;
    if ((int)len < out_len + 1) {
        snprintf(buf, len, "%s", tmp);
        return;
    }
    buf[out_len] = '\0';
    int dst_i = out_len - 1;
    int digit_count = 0;
    for (int src_i = src_len - 1; src_i >= 0; src_i--) {
        buf[dst_i--] = tmp[src_i];
        digit_count++;
        if (digit_count == 3 && src_i > 0) {
            buf[dst_i--] = ',';
            digit_count = 0;
        }
    }
}

// ============== 初始化 ==============
PortfolioApplication::PortfolioApplication()
    : home_scr_(nullptr)
    , home_wifi_lbl_(nullptr)
    , weather_scr_(nullptr)
    , portfolio_scr_(nullptr)
    , cash_scr_(nullptr)
    , fx_scr_(nullptr)
    , lbl_temp_(nullptr)
    , lbl_weather_desc_(nullptr)
    , lbl_portfolio_val_(nullptr)
    , lbl_portfolio_gain_(nullptr)
    , lbl_cash_(nullptr)
    , lbl_fx_(nullptr)
    , lbl_fx_usd_(nullptr)
    , lbl_solar_(nullptr)
    , current_screen_(Screen::HOME)
    , wifi_connected_(false)
    , wifi_just_connected_(false)
    , sntp_needed_(false)
    , ui_ready_(false)
    , clock_pending_(false)
    , solar_kwh_(0)
    , update_pending_(false)
    , clock_timer_(nullptr)
    , update_timer_(nullptr) {
}

PortfolioApplication::~PortfolioApplication() {
    if (update_timer_) esp_timer_delete(update_timer_);
}

void PortfolioApplication::Run() {
    // Nothing: all work done in Initialize() + LVGL task
    // Keep alive to satisfy framework expectation (Run() must not return)
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(10000));
        ESP_LOGI(TAG, "PortfolioApp running... (heap: %lu bytes)",
                 (unsigned long)esp_get_free_heap_size());
    }
}

void PortfolioApplication::Initialize() {
    ESP_LOGI(TAG, "====== PortfolioApplication 初始化 ======");
    fflush(stdout);  // 確保立即輸出

    // 初始化 Board singleton (這會觸發 lv_init() 透過 display 初始化)
    (void)Board::GetInstance();
    ESP_LOGI(TAG, "Board 初始化完成: %s", Board::GetInstance().GetBoardType().c_str());

    // 設定 WiFi（寫死）
    SsidManager::GetInstance().AddSsid(WIFI_SSID, WIFI_PASSWORD);
    ESP_LOGI(TAG, "WiFi 寫死設定: SSID=%s", WIFI_SSID);

    // 設定網路 callback（在 StartNetwork 之前設定）
    auto &board = Board::GetInstance();
    board.SetNetworkEventCallback([this](NetworkEvent event, const std::string &data) {
        if (event == NetworkEvent::Connected) {
            ESP_LOGI(TAG, "[NET] WiFi Connected to %s", data.c_str());
            this->wifi_connected_ = true;
            this->wifi_just_connected_ = true;  // 標記：下次 clock tick fetch RSSI
            snprintf(this->wifi_ssid_, sizeof(this->wifi_ssid_), "%s", data.c_str());
            // 不在 callback 裡抓 RSSI / Fetch（sys_evt stack 太小，TLS 會爆）
        } else if (event == NetworkEvent::Disconnected) {
            ESP_LOGI(TAG, "[NET] WiFi Disconnected");
            this->wifi_connected_ = false;
            if (this->ui_ready_ && this->home_wifi_lbl_) {
                lv_label_set_text(this->home_wifi_lbl_, "WiFi-X");
                lv_obj_set_style_text_color(this->home_wifi_lbl_, lv_color_hex(COLOR_NEGATIVE), 0);
            }
        }
    });

    // 啟動網路（WiFi 會自動連線）
    board.StartNetwork();
    ESP_LOGI(TAG, "網路啟動完成");

    // 啟動 LVGL 任務（UI 建立在任務裡，確保 LVGL 已運行）
    xTaskCreatePinnedToCore(&LvglTask, "LvglTask", 8192, this, 2, &lvgl_task_h_, 1);

    ESP_LOGI(TAG, "初始化完成");
}

// ============== LVGL Task ==============
void PortfolioApplication::LvglTask(void *arg) {
    auto *app = (PortfolioApplication *)arg;
    ESP_LOGI(TAG, "LVGL Task 啟動，等待 LVGL ready...");

    // 等 LVGL 任務排程啟動
    vTaskDelay(pdMS_TO_TICKS(500));
    ESP_LOGI(TAG, "LVGL Task 開始建立 UI");

    // 建立所有畫面（在 LVGL task 裡執行，確保 LVGL 已運行）
    app->CreateHomeScreen();
    app->CreateWeatherScreen();
    app->CreatePortfolioScreen();
    app->CreateCashScreen();
    app->CreateFxScreen();
    app->ui_ready_ = true;

    // 如果 WiFi 已經連上了（callback 可能在 ui_ready_=true 之前就觸發了），
    // 立即更新 WiFi 狀態 label
    if (app->wifi_connected_ && app->home_wifi_lbl_) {
        char buf[48];
        snprintf(buf, sizeof(buf), "%s %ddB", app->wifi_ssid_, app->wifi_rssi_);
        lv_label_set_text(app->home_wifi_lbl_, buf);
        lv_obj_set_style_text_color(app->home_wifi_lbl_, lv_color_hex(COLOR_WIFI_OK), 0);
    }

    // 同時啟動 SNTP
    setenv("TZ", "CST-8", 1);
    tzset();
    app->clock_base_time_ = 0;   // 尚未 sync
    app->clock_seconds_ = 0;
    ESP_LOGI(TAG, "[CLOCK] 等待 SNTP sync...");
    esp_sntp_config_t sntp_cfg = ESP_NETIF_SNTP_DEFAULT_CONFIG_MULTIPLE(
        2, ESP_SNTP_SERVER_LIST("tw.pool.ntp.org", "time.google.com"));
    sntp_cfg.wait_for_sync = false;
    esp_netif_sntp_init(&sntp_cfg);
    ESP_LOGI(TAG, "[NTP] SNTP 啟動 (tw.pool.ntp.org)");

    // LVGL 軟體計時器（每秒更新一次，運行在 LVGL task 內，不需 lock）
    // 使用 static app_ptr 避免 opaque lv_timer_t->user_data 問題
    static PortfolioApplication *app_ptr = app;
    lv_timer_create(
        [](lv_timer_t *) {
            auto *a = app_ptr;
            a->clock_seconds_++;
            if (a->ui_ready_ && a->home_clock_lbl_) {
                // 如果還沒有 NTP 時間，先用 time(nullptr) 顯示
                time_t now = (a->clock_base_time_ > 1000000000L)
                    ? a->clock_base_time_ + a->clock_seconds_
                    : time(nullptr);  // NTP 還沒 sync，先用系統時間
                struct tm ti;
                localtime_r(&now, &ti);
                char buf[32];
                strftime(buf, sizeof(buf), "%m/%d %H:%M:%S", &ti);
                lv_label_set_text(a->home_clock_lbl_, buf);
            }
            // 每 10 秒嘗試用 time() 當基準（如果 SNTP 還沒 sync）
            static int sync_check_counter = 0;
            sync_check_counter++;
            if (sync_check_counter >= 10) {
                sync_check_counter = 0;
                if (a->clock_base_time_ == 0) {
                    time_t now = time(nullptr);
                    ESP_LOGI(TAG, "[NTP] check: time()=%ld", (long)now);
                    if (now > 1000000000L) {
                        a->clock_base_time_ = now;
                        a->clock_seconds_ = 0;
                        ESP_LOGI(TAG, "[NTP] Fallback! Using time() as base: %ld", (long)now);
                    }
                }
            }
        },
        1000,  // 1Hz = 1000ms
        nullptr);
    ESP_LOGI(TAG, "LVGL clock timer 啟動 (1Hz)");

    // 預設顯示首頁
    lv_scr_load(app->home_scr_);
    app->current_screen_ = Screen::HOME;
    ESP_LOGI(TAG, "UI 建立完成，預設顯示首頁");

    while (1) {
        vTaskDelay(pdMS_TO_TICKS(10));



        // WiFi 連線後：在 LvglTask stack（够大）fetch RSSI 並更新 UI
        if (app->wifi_just_connected_) {
            app->wifi_just_connected_ = false;
            wifi_ap_record_t ap;
            if (esp_wifi_sta_get_ap_info(&ap) == ESP_OK) {
                app->wifi_rssi_ = ap.rssi;
                ESP_LOGI(TAG, "[WiFi] RSSI: %d dBm", ap.rssi);
            }
            // 更新 WiFi label
            if (app->ui_ready_ && app->home_wifi_lbl_) {
                char wbuf[48];
                snprintf(wbuf, sizeof(wbuf), "%s %ddB", app->wifi_ssid_, app->wifi_rssi_);
                if (lvgl_port_lock(1000)) {
                    lv_label_set_text(app->home_wifi_lbl_, wbuf);
                    lv_obj_set_style_text_color(app->home_wifi_lbl_, lv_color_hex(0x00E676), 0);
                    lvgl_port_unlock();
                }
            }
            // 立即触发一次 fetch（不等 60 秒計時器）
            app->FetchPortfolio();
            app->FetchWeather();
        }

        if (app->update_pending_) {
            app->update_pending_ = false;
            // Fetch 在 LvglTask stack（8192 bytes）執行，不用擔心 stack 爆
            app->FetchPortfolio();
            app->FetchWeather();
            if (lvgl_port_lock(50)) {
                app->UpdateHomeCards();
                lvgl_port_unlock();
            }
        }
    }
}

// ============== 更新首頁卡片 ==============
void PortfolioApplication::UpdateHomeCards() {
    if (!ui_ready_) return;

    // WiFi 狀態 re-check（確保 WiFi 在 UI 建立前就连上的情况）
    if (home_wifi_lbl_) {
        if (wifi_connected_) {
            char buf[48];
            snprintf(buf, sizeof(buf), "%s %ddB", wifi_ssid_, wifi_rssi_);
            lv_label_set_text(home_wifi_lbl_, buf);
            lv_obj_set_style_text_color(home_wifi_lbl_, lv_color_hex(0x00E676), 0);
        } else {
            lv_label_set_text(home_wifi_lbl_, "WiFi-X");
            lv_obj_set_style_text_color(home_wifi_lbl_, lv_color_hex(COLOR_TEXT), 0);
        }
    }

    if (lbl_temp_) {
        char buf[32];
        snprintf(buf, sizeof(buf), "溫度: %.0f°C", weather_.temp);
        lv_label_set_text(lbl_temp_, buf);
        lv_obj_set_style_text_color(lbl_temp_, lv_color_hex(0xFFB300), 0);
        lv_obj_set_style_text_font(lbl_temp_, &font_puhui_20_4, 0);
    }

    if (lbl_weather_desc_) {
        lv_label_set_text(lbl_weather_desc_, weather_.desc[0] ? weather_.desc : "--");
        lv_obj_set_style_text_color(lbl_weather_desc_, lv_color_hex(0x00E5FF), 0);
    }

    if (lbl_weather_humidity_) {
        char buf[32];
        snprintf(buf, sizeof(buf), "濕度: %d%%", weather_.humidity);
        lv_label_set_text(lbl_weather_humidity_, buf);
        lv_obj_set_style_text_color(lbl_weather_humidity_, lv_color_hex(0x4FC3F7), 0);
        lv_obj_set_style_text_font(lbl_weather_humidity_, &font_puhui_16_4, 0);
    }

    if (lbl_weather_updated_) {
        char buf[32];
        // time 格式: "2026-07-09 15:10:02" → 只取 "更新: 15:10"
        char *p = strstr(weather_.updated, " ");
        if (p) {
            snprintf(buf, sizeof(buf), "更新: %.5s", p + 1);  // "15:10"
        } else {
            snprintf(buf, sizeof(buf), "更新: %.19s", weather_.updated);
        }
        lv_label_set_text(lbl_weather_updated_, buf);
        lv_obj_set_style_text_color(lbl_weather_updated_, lv_color_hex(0x9E9E9E), 0);
        lv_obj_set_style_text_font(lbl_weather_updated_, &font_puhui_16_4, 0);
    }

    if (lbl_solar_) {
        char buf[32];
        if (solar_kwh_ > 0) {
            snprintf(buf, sizeof(buf), "發電: %.1f kWh", solar_kwh_);
        } else {
            snprintf(buf, sizeof(buf), "發電: -- kWh");
        }
        lv_label_set_text(lbl_solar_, buf);
        lv_obj_set_style_text_color(lbl_solar_, lv_color_hex(0xFFD54F), 0);
        lv_obj_set_style_text_font(lbl_solar_, &font_puhui_16_4, 0);
    }

    if (lbl_portfolio_val_) {
        char buf[64];
        char tmp[32];
        FormatWithCommas(tmp, sizeof(tmp), summary_.total_mktval);
        snprintf(buf, sizeof(buf), "$%s", tmp);
        lv_label_set_text(lbl_portfolio_val_, buf);
    }

    if (lbl_portfolio_gain_) {
        char buf[80];
        char tmp2[32];
        FormatWithCommas(tmp2, sizeof(tmp2), fabs(summary_.total_gain));
        snprintf(buf, sizeof(buf), "%s%s (%+.2f%%)", summary_.total_gain >= 0 ? "+" : "-", tmp2, summary_.total_gain_pct);
        lv_label_set_text(lbl_portfolio_gain_, buf);
        uint32_t color = summary_.total_gain >= 0 ? COLOR_POSITIVE : COLOR_NEGATIVE;
        lv_obj_set_style_text_color(lbl_portfolio_gain_, lv_color_hex(color), 0);
    }

    if (lbl_cash_) {
        char tmp_usd[32];
        FormatWithCommas(tmp_usd, sizeof(tmp_usd), cash_.usd_amount);
        char buf_usd[48];
        snprintf(buf_usd, sizeof(buf_usd), "USD $%s", tmp_usd);
        lv_label_set_text(lbl_cash_, buf_usd);
    }
    if (lbl_cash_twd_) {
        ESP_LOGI(TAG, "TWD label update: usd_in_twd=%.0f jpy_in_twd=%.0f",
            cash_.usd_in_twd, cash_.jpy_in_twd);
        char tmp[32];
        FormatWithCommas(tmp, sizeof(tmp), cash_.usd_in_twd);
        char buf[48];
        snprintf(buf, sizeof(buf), "TWD $%s", tmp);
        lv_label_set_text(lbl_cash_twd_, buf);
    }
    if (lbl_cash_jpy_) {
        char tmp_jpy[32];
        FormatWithCommas(tmp_jpy, sizeof(tmp_jpy), cash_.jpy_amount);
        char buf_jpy[48];
        snprintf(buf_jpy, sizeof(buf_jpy), "JPY ¥%s", tmp_jpy);
        lv_label_set_text(lbl_cash_jpy_, buf_jpy);
    }
    if (lbl_cash_jpy_twd_) {
        char tmp[32];
        FormatWithCommas(tmp, sizeof(tmp), cash_.jpy_in_twd);
        char buf[48];
        snprintf(buf, sizeof(buf), "TWD $%s", tmp);
        lv_label_set_text(lbl_cash_jpy_twd_, buf);
    }

    if (lbl_fx_usd_) {
        char buf[48];
        snprintf(buf, sizeof(buf), "USD %.3f", fx_.usd_twd);
        lv_label_set_text(lbl_fx_usd_, buf);
    }

    if (lbl_fx_) {
        char buf[48];
        snprintf(buf, sizeof(buf), "JPY %.4f", fx_.jpy_twd);
        lv_label_set_text(lbl_fx_, buf);
    }
}

// ============== JSON Fetch ==============
esp_err_t PortfolioApplication::DownloadJson(const char *url, char *buf, size_t len) {
    extern esp_err_t esp_crt_bundle_attach(void *conf);
    esp_http_client_config_t cfg = {};
    cfg.url = url;
    cfg.timeout_ms = 15000;
    cfg.crt_bundle_attach = esp_crt_bundle_attach;

    esp_http_client *client = esp_http_client_init(&cfg);
    if (!client) return ESP_FAIL;

    esp_err_t err = esp_http_client_open(client, 0);
    if (err != ESP_OK) {
        int status = esp_http_client_get_status_code(client);
        ESP_LOGW(TAG, "HTTP open failed: err=%d status=%d", err, status);
        esp_http_client_cleanup(client);
        return err;
    }

    int content_len = esp_http_client_fetch_headers(client);
    if (content_len <= 0 || content_len > (int)len - 1) {
        int status = esp_http_client_get_status_code(client);
        ESP_LOGW(TAG, "HTTP fetch failed: content_len=%d status=%d", content_len, status);
        esp_http_client_cleanup(client);
        return ESP_FAIL;
    }

    int read_len = esp_http_client_read(client, buf, len - 1);
    buf[read_len] = '\0';
    esp_http_client_cleanup(client);
    return (read_len > 0) ? ESP_OK : ESP_FAIL;
}

void PortfolioApplication::FetchPortfolio() {
    static char buf[4096];
    memset(buf, 0, sizeof(buf));

    if (DownloadJson(PORTFOLIO_JSON_URL, buf, sizeof(buf)) == ESP_OK) {
        ESP_LOGI(TAG, "Portfolio JSON received (%d bytes)", (int)strlen(buf));
        ParsePortfolioJson(buf);
        update_pending_ = true;
    } else {
        ESP_LOGW(TAG, "Portfolio fetch failed");
    }
}

void PortfolioApplication::FetchWeather() {
    static char buf[1024];
    memset(buf, 0, sizeof(buf));

    if (DownloadJson(WEATHER_JSON_URL, buf, sizeof(buf)) == ESP_OK) {
        ESP_LOGI(TAG, "Weather JSON received (%d bytes)", (int)strlen(buf));
        ParseWeatherJson(buf);
        update_pending_ = true;
    } else {
        ESP_LOGW(TAG, "Weather fetch failed");
    }
}

// ============== JSON 解析（符合 R2 實際格式） ==============
void PortfolioApplication::ParsePortfolioJson(const char *json) {
    // Flatten JSON: replace newlines/spaces with single space for robust parsing
    // NOTE: static buffer to avoid stack overflow (event task has small stack)
    static char flat[4096];
    int j = 0;
    for (int i = 0; json[i] && j < (int)sizeof(flat) - 1; i++) {
        if (json[i] == '\n' || json[i] == '\r' || json[i] == '\t') {
            if (j > 0 && flat[j-1] != ' ') flat[j++] = ' ';
        } else {
            flat[j++] = json[i];
        }
    }
    flat[j] = '\0';

    ESP_LOGI(TAG, "[DEBUG] ParseWeather: temp=%.0f desc=[%s] humidity=%d updated=[%s]", weather_.temp, weather_.desc[0] ? weather_.desc : "(empty)", weather_.humidity, weather_.updated[0] ? weather_.updated : "(empty)");
    const char *p = strstr(flat, "\"total_cost\":");
    if (p) sscanf(p, "\"total_cost\":%f", &summary_.total_cost);

    p = strstr(flat, "\"total_mktval\":");
    if (p) sscanf(p, "\"total_mktval\":%f", &summary_.total_mktval);

    p = strstr(flat, "\"total_gain\":");
    if (p) sscanf(p, "\"total_gain\":%f", &summary_.total_gain);

    p = strstr(flat, "\"total_gain_pct\":");
    if (p) sscanf(p, "\"total_gain_pct\":%f", &summary_.total_gain_pct);

    p = strstr(flat, "\"tw\"");
    if (p) {
        const char *cp = strstr(p, "\"mktval\":");
        if (cp) sscanf(cp, "\"mktval\":%f", &tw_.mktval);
        cp = strstr(p, "\"gain\":");
        if (cp) sscanf(cp, "\"gain\":%f", &tw_.gain);
        cp = strstr(p, "\"gain_pct\":");
        if (cp) sscanf(cp, "\"gain_pct\":%f", &tw_.gain_pct);
    }

    p = strstr(flat, "\"usd_twd\":");
    if (p) sscanf(p, "\"usd_twd\":%f", &fx_.usd_twd);
    p = strstr(flat, "\"jpy_twd\":");
    if (p) sscanf(p, "\"jpy_twd\":%f", &fx_.jpy_twd);

    // Search for "cash" block first to avoid matching fx.usd_twd
    p = strstr(flat, "\"cash\"");
    if (p) {
        const char *cp = strstr(p, "\"usd\"");
        if (cp) {
            const char *ap = strstr(cp, "\"amount\":");
            if (ap) sscanf(ap, "\"amount\":%f", &cash_.usd_amount);
            ap = strstr(cp, "\"in_twd\":");
            if (ap) sscanf(ap, "\"in_twd\":%f", &cash_.usd_in_twd);
        }
        cp = strstr(p, "\"jpy\"");
        if (cp) {
            const char *ap = strstr(cp, "\"amount\":");
            if (ap) sscanf(ap, "\"amount\":%f", &cash_.jpy_amount);
            ap = strstr(cp, "\"in_twd\":");
            if (ap) sscanf(ap, "\"in_twd\":%f", &cash_.jpy_in_twd);
        }
    }

    ESP_LOGI(TAG, "Cash parse: USD=%.0f in_twd=%.0f, JPY=%.0f in_twd=%.0f",
        cash_.usd_amount, cash_.usd_in_twd, cash_.jpy_amount, cash_.jpy_in_twd);
    ESP_LOGI(TAG, "Summary: mktval=%.0f gain=%.0f (%.2f%%) fx=%.3f/%.4f",
        summary_.total_mktval, summary_.total_gain, summary_.total_gain_pct,
        fx_.usd_twd, fx_.jpy_twd);

    // Parse solar_kwh (if present in JSON)
    p = strstr(flat, "\"solar_kwh\":");
    if (p) sscanf(p, "\"solar_kwh\":%f", &solar_kwh_);
    ESP_LOGI(TAG, "Solar kWh: %.1f", solar_kwh_);
}

void PortfolioApplication::ParseWeatherJson(const char *json) {
    // R2 weather JSON: { "temp": 32.0, "desc": "晴", "humidity": 61, "feels_like": 35.0, "time": "2026-07-10 10:00" }
    const char *p = strstr(json, "\"temp\":");
    if (p) sscanf(p, "\"temp\":%f", &weather_.temp);

    p = strstr(json, "\"desc\": \"");
    if (p) {
        const char *start = p + 9;
        const char *end = strchr(start, '\"');
        if (end) {
            int len = (int)(end - start);
            if (len > (int)sizeof(weather_.desc) - 1) len = sizeof(weather_.desc) - 1;
            strncpy(weather_.desc, start, len);
            weather_.desc[len] = '\0';
        }
    }

    p = strstr(json, "\"humidity\":");
    if (p) sscanf(p, "\"humidity\":%d", &weather_.humidity);

    p = strstr(json, "\"feels_like\":");
    if (p) sscanf(p, "\"feels_like\":%f", &weather_.feels_like);

    p = strstr(json, "\"time\": \"");
    if (p) {
        const char *start = p + 9;
        const char *end = strchr(start, '\"');
        if (end) {
            int len = (int)(end - start);
            if (len > (int)sizeof(weather_.updated) - 1) len = sizeof(weather_.updated) - 1;
            strncpy(weather_.updated, start, len);
            weather_.updated[len] = '\0';
        }
    }

    ESP_LOGI(TAG, "Weather: %.1f°C %s humidity=%d%%",
        weather_.temp, weather_.desc, weather_.humidity);
}

// ============== UI 建立（全部在 LVGL Task 裡執行） ==============
void PortfolioApplication::CreateHomeScreen() {
    ESP_LOGI(TAG, "CreateHomeScreen 開始");
    home_scr_ = lv_obj_create(NULL);
    lv_obj_set_style_bg_color(home_scr_, lv_color_hex(COLOR_BG), 0);
    lv_obj_set_scrollbar_mode(home_scr_, LV_SCROLLBAR_MODE_OFF);
    lv_obj_remove_flag(home_scr_, LV_OBJ_FLAG_SCROLLABLE);
    // Header (y=0, h=45, 含 WiFi 狀態 + 時鐘)
    lv_obj_t *header = lv_obj_create(home_scr_);
    lv_obj_set_size(header, 480, 45);
    lv_obj_set_pos(header, 0, 0);
    lv_obj_set_style_bg_color(header, lv_color_hex(0x111122), 0);
    lv_obj_set_style_border_width(header, 0, 0);
    lv_obj_set_style_radius(header, 0, 0);
    lv_obj_remove_flag(header, LV_OBJ_FLAG_SCROLLABLE);

    lv_obj_t *lbl;

    home_wifi_lbl_ = lv_label_create(header);
    lv_label_set_text(home_wifi_lbl_, "WiFi");
    lv_obj_set_pos(home_wifi_lbl_, 10, 2);
    lv_obj_set_style_text_font(home_wifi_lbl_, &lv_font_montserrat_14, 0);

    home_clock_lbl_ = lv_label_create(header);
    lv_label_set_text(home_clock_lbl_, "--/-- --:--:--");
    lv_obj_set_pos(home_clock_lbl_, 330, 2);
    lv_obj_set_style_text_color(home_clock_lbl_, lv_color_hex(COLOR_TEXT), 0);
    lv_obj_set_style_text_font(home_clock_lbl_, &lv_font_montserrat_14, 0);

    // === 天氣卡片 (y=50, h=100, 滿版) ===
    lv_obj_t *card = CreateCard(home_scr_, 50, 100);

    // 標題
    lbl = lv_label_create(card);
    lv_label_set_text(lbl, "天氣");
    lv_obj_set_pos(lbl, 10, 5);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_SUBTEXT), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);

    // === Line 1: 溫度（左）| 天氣描述（中）| 更新時間（右）===
    // 溫度（左，橙黃色）
    lbl = lv_label_create(card);
    lv_label_set_text(lbl, "溫度: --°C");
    lv_obj_set_pos(lbl, 10, 22);
    lv_obj_set_style_text_color(lbl, lv_color_hex(0xFFB300), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_20_4, 0);
    lbl_temp_ = lbl;

    // 天氣描述（中，青藍色）
    lbl_weather_desc_ = lv_label_create(card);
    lv_label_set_text(lbl_weather_desc_, "--");
    lv_obj_set_pos(lbl_weather_desc_, 180, 22);
    lv_obj_set_size(lbl_weather_desc_, 195, 24);
    lv_obj_set_style_text_color(lbl_weather_desc_, lv_color_hex(0x00E5FF), 0);
    lv_obj_set_style_text_font(lbl_weather_desc_, &font_puhui_16_4, 0);

    // 更新時間（右，灰色）
    lbl_weather_updated_ = lv_label_create(card);
    lv_label_set_text(lbl_weather_updated_, "更新: --:--");
    lv_obj_set_pos(lbl_weather_updated_, 330, 22);
    lv_obj_set_style_text_color(lbl_weather_updated_, lv_color_hex(0x9E9E9E), 0);
    lv_obj_set_style_text_font(lbl_weather_updated_, &font_puhui_16_4, 0);

    // === Line 2: 濕度（左）| 累積發電量（右）===
    // 濕度（左，淺藍色）
    lbl = lv_label_create(card);
    lv_label_set_text(lbl, "濕度: --%%");
    lv_obj_set_pos(lbl, 10, 50);
    lv_obj_set_style_text_color(lbl, lv_color_hex(0x4FC3F7), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);
    lbl_weather_humidity_ = lbl;

    // 太陽能發電量（右，金色）
    lbl = lv_label_create(card);
    lv_label_set_text(lbl, "發電: -- kWh");
    lv_obj_set_pos(lbl, 180, 50);
    lv_obj_set_style_text_color(lbl, lv_color_hex(0xFFD54F), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);
    lbl_solar_ = lbl;

    // 箭頭（右上角）
    lbl = lv_label_create(card);
    lv_label_set_text(lbl, ">");
    lv_obj_set_pos(lbl, 440, 22);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_SUBTEXT), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);

    lv_obj_set_user_data(card, this);
    lv_obj_add_event_cb(card, [](lv_event_t *e) {
        auto *app = (PortfolioApplication *)lv_event_get_user_data(e);
        app->SwitchScreen(Screen::WEATHER);
    }, LV_EVENT_CLICKED, this);

    // === 持股 + 現金 + 匯率 2x2 網格 (y=155) ===
    // 左：持股滿高 | 右上：現金 | 右下：匯率
    // 左 x=8, w=232  | 右 x=248, w=224  | gap=8

    // --- 持股卡片（左，滿高度）---
    card = CreateCard(home_scr_, 155, 290);
    lv_obj_set_pos(card, 8, 155);
    lv_obj_set_size(card, 232, 290);

    lbl = lv_label_create(card);
    lv_label_set_text(lbl, "持股總市值");
    lv_obj_set_pos(lbl, 10, 8);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_SUBTEXT), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);

    lbl = lv_label_create(card);
    lv_label_set_text(lbl, "$ --");
    lv_obj_set_pos(lbl, 10, 30);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_TEXT), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_20_4, 0);
    lbl_portfolio_val_ = lbl;

    lbl = lv_label_create(card);
    lv_label_set_text(lbl, "$ -- (--%)");
    lv_obj_set_pos(lbl, 10, 70);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_POSITIVE), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);
    lbl_portfolio_gain_ = lbl;

    lbl = lv_label_create(card);
    lv_label_set_text(lbl, ">");
    lv_obj_set_pos(lbl, 195, 75);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_SUBTEXT), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);

    lv_obj_set_user_data(card, this);
    lv_obj_add_event_cb(card, [](lv_event_t *e) {
        auto *app = (PortfolioApplication *)lv_event_get_user_data(e);
        app->SwitchScreen(Screen::PORTFOLIO);
    }, LV_EVENT_CLICKED, this);

    // --- 現金卡片（右上，4行）---
    card = CreateCard(home_scr_, 155, 140);
    lv_obj_set_pos(card, 248, 155);
    lv_obj_set_size(card, 224, 140);

    lbl = lv_label_create(card);
    lv_label_set_text(lbl, "外幣現金");
    lv_obj_set_pos(lbl, 10, 5);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_SUBTEXT), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);

    lbl = lv_label_create(card);
    lv_label_set_text(lbl, "USD $--");
    lv_obj_set_pos(lbl, 10, 25);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_MONEY), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);
    lbl_cash_ = lbl;

    lbl = lv_label_create(card);
    lv_label_set_text(lbl, "TWD $--");
    lv_obj_set_pos(lbl, 10, 45);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_SUBTEXT), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);
    lbl_cash_twd_ = lbl;

    lbl = lv_label_create(card);
    lv_label_set_text(lbl, "JPY ¥--");
    lv_obj_set_pos(lbl, 10, 65);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_MONEY), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);
    lbl_cash_jpy_ = lbl;

    lbl = lv_label_create(card);
    lv_label_set_text(lbl, "TWD $--");
    lv_obj_set_pos(lbl, 10, 85);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_SUBTEXT), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);
    lbl_cash_jpy_twd_ = lbl;

    lbl = lv_label_create(card);
    lv_label_set_text(lbl, ">");
    lv_obj_set_pos(lbl, 185, 45);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_SUBTEXT), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);

    lv_obj_set_user_data(card, this);
    lv_obj_add_event_cb(card, [](lv_event_t *e) {
        auto *app = (PortfolioApplication *)lv_event_get_user_data(e);
        app->SwitchScreen(Screen::CASH);
    }, LV_EVENT_CLICKED, this);

    // --- 匯率卡片（右下）---
    card = CreateCard(home_scr_, 303, 140);
    lv_obj_set_pos(card, 248, 303);
    lv_obj_set_size(card, 224, 140);

    lbl = lv_label_create(card);
    lv_label_set_text(lbl, "匯率");
    lv_obj_set_pos(lbl, 10, 8);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_SUBTEXT), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);

    lbl = lv_label_create(card);
    lv_label_set_text(lbl, "USD --");
    lv_obj_set_pos(lbl, 10, 30);
    lv_obj_set_style_text_color(lbl, lv_color_hex(0xCE93D8), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);
    lbl_fx_usd_ = lbl;

    lbl = lv_label_create(card);
    lv_label_set_text(lbl, "JPY --");
    lv_obj_set_pos(lbl, 10, 55);
    lv_obj_set_style_text_color(lbl, lv_color_hex(0xCE93D8), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);
    lbl_fx_ = lbl;

    lbl = lv_label_create(card);
    lv_label_set_text(lbl, ">");
    lv_obj_set_pos(lbl, 185, 35);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_SUBTEXT), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);

    lv_obj_set_user_data(card, this);
    lv_obj_add_event_cb(card, [](lv_event_t *e) {
        auto *app = (PortfolioApplication *)lv_event_get_user_data(e);
        app->SwitchScreen(Screen::FX);
    }, LV_EVENT_CLICKED, this);

    ESP_LOGI(TAG, "CreateHomeScreen 完成");
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_SUBTEXT), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);

    lv_obj_set_user_data(card, this);
    lv_obj_add_event_cb(card, [](lv_event_t *e) {
        auto *app = (PortfolioApplication *)lv_event_get_user_data(e);
        app->SwitchScreen(Screen::FX);
    }, LV_EVENT_CLICKED, this);

    ESP_LOGI(TAG, "CreateHomeScreen 完成");
}

lv_obj_t* PortfolioApplication::CreateCard(lv_obj_t *parent, int y, int h) {
    lv_obj_t *card = lv_obj_create(parent);
    lv_obj_set_size(card, 460, h);
    lv_obj_set_pos(card, 10, y);
    lv_obj_set_style_bg_color(card, lv_color_hex(COLOR_CARD), 0);
    lv_obj_set_style_radius(card, 4, 0);
    lv_obj_set_style_border_color(card, lv_color_hex(COLOR_CARD_LINE), 0);
    lv_obj_set_style_border_width(card, 1, 0);
    lv_obj_set_scrollbar_mode(card, LV_SCROLLBAR_MODE_OFF);
    lv_obj_remove_flag(card, LV_OBJ_FLAG_SCROLLABLE);
    return card;
}

void PortfolioApplication::CreateBackBtn(lv_obj_t *parent) {
    lv_obj_t *btn = lv_btn_create(parent);
    lv_obj_set_size(btn, 70, 32);
    lv_obj_set_pos(btn, 5, 5);
    lv_obj_set_style_bg_color(btn, lv_color_hex(COLOR_CARD), 0);
    lv_obj_set_style_radius(btn, 4, 0);

    lv_obj_t *lbl = lv_label_create(btn);
    lv_label_set_text(lbl, "< 返回");
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_TEXT), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);
    lv_obj_center(lbl);

    lv_obj_set_user_data(btn, this);
    lv_obj_add_event_cb(btn, BackBtnCallback, LV_EVENT_CLICKED, this);
}

// ============== Detail 畫面 ==============
void PortfolioApplication::CreateWeatherScreen() {
    weather_scr_ = lv_obj_create(NULL);
    lv_obj_set_scrollbar_mode(weather_scr_, LV_SCROLLBAR_MODE_OFF);
    lv_obj_remove_flag(weather_scr_, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_style_bg_color(weather_scr_, lv_color_hex(COLOR_BG), 0);
    CreateBackBtn(weather_scr_);

    lv_obj_t *lbl = lv_label_create(weather_scr_);
    lv_label_set_text(lbl, "☁️ 天氣詳情");
    lv_obj_set_pos(lbl, 90, 8);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_TEXT), 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_16, 0);

    lbl = lv_label_create(weather_scr_);
    lv_label_set_text(lbl, "--°C");
    lv_obj_set_pos(lbl, 20, 50);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_TEXT), 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_40, 0);

    lbl = lv_label_create(weather_scr_);
    lv_label_set_text(lbl, weather_.desc[0] ? weather_.desc : "加載中...");
    lv_obj_set_pos(lbl, 20, 110);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_SUBTEXT), 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_16, 0);

    lbl = lv_label_create(weather_scr_);
    char buf[32];
    snprintf(buf, sizeof(buf), "💧 濕度: %d%%", weather_.humidity);
    lv_label_set_text(lbl, buf);
    lv_obj_set_pos(lbl, 20, 150);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_TEXT), 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_14, 0);

    ESP_LOGI(TAG, "CreateWeatherScreen 完成");
}

void PortfolioApplication::CreatePortfolioScreen() {
    portfolio_scr_ = lv_obj_create(NULL);
    lv_obj_set_scrollbar_mode(portfolio_scr_, LV_SCROLLBAR_MODE_OFF);
    lv_obj_remove_flag(portfolio_scr_, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_style_bg_color(portfolio_scr_, lv_color_hex(COLOR_BG), 0);
    CreateBackBtn(portfolio_scr_);

    lv_obj_t *lbl = lv_label_create(portfolio_scr_);
    lv_label_set_text(lbl, "📊 持股總攬");
    lv_obj_set_pos(lbl, 90, 8);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_TEXT), 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_16, 0);

    lbl = lv_label_create(portfolio_scr_);
    lv_label_set_text(lbl, "總市值");
    lv_obj_set_pos(lbl, 20, 50);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_SUBTEXT), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);

    lbl = lv_label_create(portfolio_scr_);
    char buf[32];
    FormatWithCommas(buf, sizeof(buf), summary_.total_mktval);
    lv_label_set_text(lbl, buf);
    lv_obj_set_pos(lbl, 20, 65);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_TEXT), 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_28, 0);

    lbl = lv_label_create(portfolio_scr_);
    lv_label_set_text(lbl, "💰 台股");
    lv_obj_set_pos(lbl, 20, 115);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_SUBTEXT), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);

    lbl = lv_label_create(portfolio_scr_);
    snprintf(buf, sizeof(buf), "$%.0f (%+.2f%%)", tw_.mktval, tw_.gain_pct);
    lv_label_set_text(lbl, buf);
    lv_obj_set_pos(lbl, 20, 130);
    lv_obj_set_style_text_color(lbl, tw_.gain >= 0 ? lv_color_hex(COLOR_POSITIVE) : lv_color_hex(COLOR_NEGATIVE), 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_14, 0);

    lbl = lv_label_create(portfolio_scr_);
    lv_label_set_text(lbl, "💵 美股");
    lv_obj_set_pos(lbl, 20, 160);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_SUBTEXT), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);

    lbl = lv_label_create(portfolio_scr_);
    snprintf(buf, sizeof(buf), "$%.0f (%+.2f%%)", us_.mktval, us_.gain_pct);
    lv_label_set_text(lbl, buf);
    lv_obj_set_pos(lbl, 20, 175);
    lv_obj_set_style_text_color(lbl, us_.gain >= 0 ? lv_color_hex(COLOR_POSITIVE) : lv_color_hex(COLOR_NEGATIVE), 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_14, 0);

    ESP_LOGI(TAG, "CreatePortfolioScreen 完成");
}

void PortfolioApplication::CreateCashScreen() {
    cash_scr_ = lv_obj_create(NULL);
    lv_obj_set_scrollbar_mode(cash_scr_, LV_SCROLLBAR_MODE_OFF);
    lv_obj_remove_flag(cash_scr_, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_style_bg_color(cash_scr_, lv_color_hex(COLOR_BG), 0);
    CreateBackBtn(cash_scr_);

    lv_obj_t *lbl = lv_label_create(cash_scr_);
    lv_label_set_text(lbl, "現金");
    lv_obj_set_pos(lbl, 90, 8);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_TEXT), 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_16, 0);

    lbl = lv_label_create(cash_scr_);
    lv_label_set_text(lbl, "USD");
    lv_obj_set_pos(lbl, 20, 50);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_SUBTEXT), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);

    lbl = lv_label_create(cash_scr_);
    char buf[64];
    snprintf(buf, sizeof(buf), "$%.2f", cash_.usd_amount);
    lv_label_set_text(lbl, buf);
    lv_obj_set_pos(lbl, 20, 65);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_MONEY), 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_28, 0);

    lbl = lv_label_create(cash_scr_);
    snprintf(buf, sizeof(buf), "≈ NT$ %.0f", cash_.usd_in_twd);
    lv_label_set_text(lbl, buf);
    lv_obj_set_pos(lbl, 20, 100);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_SUBTEXT), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);

    lbl = lv_label_create(cash_scr_);
    lv_label_set_text(lbl, "JPY");
    lv_obj_set_pos(lbl, 20, 140);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_SUBTEXT), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);

    lbl = lv_label_create(cash_scr_);
    snprintf(buf, sizeof(buf), "¥%.0f", cash_.jpy_amount);
    lv_label_set_text(lbl, buf);
    lv_obj_set_pos(lbl, 20, 155);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_MONEY), 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_28, 0);

    lbl = lv_label_create(cash_scr_);
    snprintf(buf, sizeof(buf), "≈ NT$ %.0f", cash_.jpy_in_twd);
    lv_label_set_text(lbl, buf);
    lv_obj_set_pos(lbl, 20, 190);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_SUBTEXT), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);

    ESP_LOGI(TAG, "CreateCashScreen 完成");
}

void PortfolioApplication::CreateFxScreen() {
    fx_scr_ = lv_obj_create(NULL);
    lv_obj_set_scrollbar_mode(fx_scr_, LV_SCROLLBAR_MODE_OFF);
    lv_obj_remove_flag(fx_scr_, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_style_bg_color(fx_scr_, lv_color_hex(COLOR_BG), 0);
    CreateBackBtn(fx_scr_);

    lv_obj_t *lbl = lv_label_create(fx_scr_);
    lv_label_set_text(lbl, "匯率");
    lv_obj_set_pos(lbl, 90, 8);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_TEXT), 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_16, 0);

    lbl = lv_label_create(fx_scr_);
    lv_label_set_text(lbl, "USD / TWD");
    lv_obj_set_pos(lbl, 20, 50);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_SUBTEXT), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);

    lbl = lv_label_create(fx_scr_);
    char buf[48];
    snprintf(buf, sizeof(buf), "%.4f", fx_.usd_twd);
    lv_label_set_text(lbl, buf);
    lv_obj_set_pos(lbl, 20, 65);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_TEXT), 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_28, 0);

    lbl = lv_label_create(fx_scr_);
    lv_label_set_text(lbl, "JPY / TWD");
    lv_obj_set_pos(lbl, 20, 115);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_SUBTEXT), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);

    lbl = lv_label_create(fx_scr_);
    snprintf(buf, sizeof(buf), "%.4f", fx_.jpy_twd);
    lv_label_set_text(lbl, buf);
    lv_obj_set_pos(lbl, 20, 130);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_TEXT), 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_28, 0);

    lbl = lv_label_create(fx_scr_);
    snprintf(buf, sizeof(buf), "更新: %s", fx_.updated);
    lv_label_set_text(lbl, buf);
    lv_obj_set_pos(lbl, 20, 180);
    lv_obj_set_style_text_color(lbl, lv_color_hex(COLOR_SUBTEXT), 0);
    lv_obj_set_style_text_font(lbl, &font_puhui_16_4, 0);

    ESP_LOGI(TAG, "CreateFxScreen 完成");
}

// ============== 畫面切換 ==============
void PortfolioApplication::SwitchScreen(Screen s) {
    current_screen_ = s;
    lv_obj_t *scr = nullptr;
    switch (s) {
        case Screen::HOME: scr = home_scr_; break;
        case Screen::WEATHER: scr = weather_scr_; break;
        case Screen::PORTFOLIO: scr = portfolio_scr_; break;
        case Screen::CASH: scr = cash_scr_; break;
        case Screen::FX: scr = fx_scr_; break;
    }
    if (scr) lv_scr_load(scr);
}

// ============== 按鈕事件 ==============
void PortfolioApplication::HomeCardClickCallback(lv_event_t *e) {
    auto *app = (PortfolioApplication *)lv_event_get_user_data(e);
    int id = (int)(intptr_t)lv_event_get_user_data(e);

    Screen s = Screen::HOME;
    switch (id) {
        case 0: s = Screen::WEATHER; break;
        case 1: s = Screen::PORTFOLIO; break;
        case 2: s = Screen::CASH; break;
        case 3: s = Screen::FX; break;
        default: s = Screen::HOME; break;
    }
    app->SwitchScreen(s);
}

void PortfolioApplication::BackBtnCallback(lv_event_t *e) {
    auto *app = (PortfolioApplication *)lv_event_get_user_data(e);
    if (app) app->SwitchScreen(Screen::HOME);
}
