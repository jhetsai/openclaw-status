# Get all source files recursively from src directory
file(GLOB_RECURSE SRC_FILES "src/*.c")

idf_component_register(
    SRCS ${SRC_FILES}
    INCLUDE_DIRS
        "include"
    PRIV_INCLUDE_DIRS
        "src"
    REQUIRES esp_timer
)

# Disable -Werror=format for this component (uint32_t vs %d in ESP-IDF v5.4.2)
target_compile_options(${COMPONENT_LIB} PRIVATE -Wno-error=format -Wno-error=format=)
