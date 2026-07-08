#include "application.h"
#include "board.h"
#include "portfolio_display.h"
#include "settings.h"
#include "system_info.h"
#include "display/lcd_display.h"

#include <esp_log.h>
#include <esp_http_client.h>
#include <esp_wifi.h>
#include <nvs_flash.h>
#include <nvs.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <cJSON.h>

static const char* TAG = "PortfolioApp";

// R2 JSON URL - update with your actual bucket URL
#define PORTFOLIO_JSON_URL "https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/assets/esp32_portfolio.json"
#define FETCH_INTERVAL_MS 30000  // Refresh every 30 seconds

static PortfolioDisplay* g_portfolio_display = nullptr;

class PortfolioApplication {
public:
    PortfolioApplication() {}

    void Initialize() {
        ESP_LOGI(TAG, "=== Portfolio Dashboard v1.0 ===");

        // Initialize NVS
        esp_err_t ret = nvs_flash_init();
        if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
            ESP_ERROR_CHECK(nvs_flash_erase());
            ret = nvs_flash_init();
        }
        ESP_ERROR_CHECK(ret);

        // Initialize Board (LCD, Touch, AXP2101, etc.)
        auto& board = Board::GetInstance();
        ESP_LOGI(TAG, "Board SKU: %s", BOARD_NAME);

        // Get display and initialize portfolio UI
        auto display = board.GetDisplay();
        if (display) {
            g_portfolio_display = new PortfolioDisplay();
            // The display is already initialized by board, we just setup our UI
            g_portfolio_display->SetupPortfolioUI();
            ESP_LOGI(TAG, "Portfolio UI initialized");
        }

        // Initialize WiFi
        InitializeWiFi();

        // Start fetch task
        xTaskCreatePinnedToCore(FetchTask, "portfolio_fetch", 8192, this, 5, NULL, 1);
    }

    void Run() {
        while (true) {
            vTaskDelay(pdMS_TO_TICKS(1000));
        }
    }

private:
    void InitializeWiFi() {
        ESP_LOGI(TAG, "Initializing WiFi...");

        wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
        ESP_ERROR_CHECK(esp_wifi_init(&cfg));

        // Load saved WiFi config
        Settings settings("wifi", true);
        std::string ssid = settings.GetString("ssid");
        std::string password = settings.GetString("password");

        if (ssid.empty()) {
            ESP_LOGW(TAG, "No WiFi config found, starting AP mode");
            StartAPMode();
        } else {
            ESP_LOGI(TAG, "WiFi config found: %s", ssid.c_str());
            StartSTAMode(ssid.c_str(), password.c_str());
        }
    }

    void StartAPMode() {
        ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_AP));
        wifi_config_t ap_config = {};
        strcpy((char*)ap_config.ap.ssid, "PortfolioDash");
        strcpy((char*)ap_config.ap.password, "12345678");
        ap_config.ap.authmode = WIFI_AUTH_WPA_WPA2_PSK;
        ap_config.ap.max_connection = 4;
        ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_AP, &ap_config));
        ESP_ERROR_CHECK(esp_wifi_start());
        ESP_LOGI(TAG, "AP started: PortfolioDash");
    }

    void StartSTAMode(const char* ssid, const char* password) {
        ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
        wifi_config_t sta_config = {};
        strcpy((char*)sta_config.sta.ssid, ssid);
        strcpy((char*)sta_config.sta.password, password);
        sta_config.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;
        ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &sta_config));
        ESP_ERROR_CHECK(esp_wifi_start());
        ESP_LOGI(TAG, "WiFi STA started, connecting to %s...", ssid);
    }

    static void FetchTask(void* param) {
        auto* app = static_cast<PortfolioApplication*>(param);
        int fetch_count = 0;

        while (true) {
            vTaskDelay(pdMS_TO_TICKS(FETCH_INTERVAL_MS));

            if (fetch_count == 0) {
                app->FetchPortfolioJson();
            }
            fetch_count++;
            if (fetch_count > 10) fetch_count = 0;  // Occasionally refresh
        }
    }

    void FetchPortfolioJson() {
        ESP_LOGI(TAG, "Fetching portfolio JSON...");

        esp_http_client_config_t config = {
            .url = PORTFOLIO_JSON_URL,
            .timeout_ms = 10000,
        };

        esp_http_client_handle_t client = esp_http_client_init(&config);
        if (!client) {
            ESP_LOGE(TAG, "Failed to init HTTP client");
            return;
        }

        esp_err_t err = esp_http_client_open(client, 0);
        if (err != ESP_OK) {
            ESP_LOGE(TAG, "Failed to open HTTP connection: %s", esp_err_to_name(err));
            esp_http_client_cleanup(client);
            return;
        }

        int content_length = esp_http_client_fetch_headers(client);
        if (content_length <= 0) {
            ESP_LOGW(TAG, "No content or content_length=%d", content_length);
            esp_http_client_cleanup(client);
            return;
        }

        std::string response;
        response.resize(content_length + 1);

        int read_len = esp_http_client_read(client, &response[0], content_length);
        if (read_len > 0) {
            response[read_len] = '\0';

            // Parse JSON
            cJSON* root = cJSON_Parse(response.c_str());
            if (root) {
                ESP_LOGI(TAG, "JSON parsed successfully!");
                if (g_portfolio_display) {
                    g_portfolio_display->UpdatePortfolioData(root);
                }
                cJSON_Delete(root);
            } else {
                ESP_LOGE(TAG, "JSON parse error");
            }
        } else {
            ESP_LOGE(TAG, "HTTP read error");
        }

        esp_http_client_cleanup(client);
    }
};

// Static application instance
static PortfolioApplication* s_app = nullptr;

extern "C" void app_main(void) {
    s_app = new PortfolioApplication();
    s_app->Initialize();
    s_app->Run();
    // Never returns
}
