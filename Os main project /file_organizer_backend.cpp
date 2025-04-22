#include <iostream>
#include <vector>
#include <string>
#include <filesystem>
#include <ctime>
#include <cstring>
#include <map>
#include <chrono>
#include <algorithm>  

extern "C" {
   
    char** get_directory_contents(const char* directory_path) {
        std::vector<std::string> files;
        try {
            for (const auto& entry : std::filesystem::directory_iterator(directory_path)) {
                if (!entry.is_directory() && entry.path().filename().string()[0] != '.') {
                    files.push_back(entry.path().string());
                }
            }
        } catch (...) {
            return nullptr;  
        }

        
        char** result = (char**)malloc((files.size() + 1) * sizeof(char*));
        for (size_t i = 0; i < files.size(); ++i) {
            result[i] = (char*)malloc((files[i].size() + 1) * sizeof(char));
            strcpy(result[i], files[i].c_str());
        }
        result[files.size()] = nullptr;  
        return result;
    }

    
    bool copy_file(const char* src, const char* dest) {
        try {
            std::filesystem::copy(src, dest, std::filesystem::copy_options::overwrite_existing);
            return true;
        } catch (...) {
            return false;
        }
    }

    
    bool move_file(const char* src, const char* dest) {
        try {
            std::filesystem::rename(src, dest);
            return true;
        } catch (...) {
            return false;
        }
    }

    
    bool delete_file(const char* path) {
        try {
            std::filesystem::remove_all(path);
            return true;
        } catch (...) {
            return false;
        }
    }

    
    bool organize_by_date(const char* directory) {
        try {
            for (const auto& entry : std::filesystem::directory_iterator(directory)) {
                if (entry.is_regular_file()) {
                    auto modified_time = entry.last_write_time();
                    
                    auto sctp = std::chrono::time_point_cast<std::chrono::system_clock::duration>(
                        modified_time - std::filesystem::file_time_type::clock::now() + std::chrono::system_clock::now());
                    std::time_t cftime = std::chrono::system_clock::to_time_t(sctp);
                    std::tm* timeinfo = std::localtime(&cftime);

                    char date_folder[11];
                    std::strftime(date_folder, sizeof(date_folder), "%Y-%m-%d", timeinfo);

                    std::string new_path = std::string(directory) + "/" + date_folder;
                    std::filesystem::create_directories(new_path);
                    std::filesystem::copy(entry.path(), new_path + "/" + entry.path().filename().string(),
                                          std::filesystem::copy_options::overwrite_existing);
                }
            }
            return true;
        } catch (...) {
            return false;
        }
    }

    
    bool organize_by_type(const char* directory) {
        try {
            std::map<std::string, std::vector<std::string>> categories = {
                {"Images", {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}},
                {"Videos", {".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv", ".webm"}},
                {"Audio", {".mp3", ".wav", ".ogg", ".flac", ".aac", ".wma"}},
                {"Documents", {".pdf", ".doc", ".docx", ".rtf", ".tex"}},
                {"Spreadsheets", {".xls", ".xlsx", ".csv"}},
                {"Presentations", {".ppt", ".pptx"}},
                {"Text", {".txt", ".md", ".log"}},
                {"Archives", {".zip", ".rar", ".7z", ".tar", ".gz", ".iso"}},
                {"Executables", {".exe", ".msi", ".app"}},
                {"OneNote", {".one", ".onetoc2"}}
            };

            for (const auto& entry : std::filesystem::directory_iterator(directory)) {
                if (entry.is_regular_file()) {
                    std::string ext = entry.path().extension().string();
                    std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);  // Convert to lowercase
                    std::string category = "Others";

                    for (const auto& [cat_name, extensions] : categories) {
                        if (std::find(extensions.begin(), extensions.end(), ext) != extensions.end()) {
                            category = cat_name;
                            break;
                        }
                    }

                    std::string new_path = std::string(directory) + "/" + category;
                    std::filesystem::create_directories(new_path);
                    std::filesystem::copy(entry.path(), new_path + "/" + entry.path().filename().string(),
                                          std::filesystem::copy_options::overwrite_existing);
                }
            }
            return true;
        } catch (...) {
            return false;
        }
    }
}
