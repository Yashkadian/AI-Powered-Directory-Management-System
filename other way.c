#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include <direct.h>

void create_directory(const char* path) {
    _mkdir(path);
}

void move_file(const char* file_path, const char* dest_folder, const char* file_name) {
    char new_path[MAX_PATH];
    snprintf(new_path, MAX_PATH, "%s\\%s", dest_folder, file_name);
    MoveFile(file_path, new_path);
}

void remove_quotes(char* str) {
    size_t len = strlen(str);
    if (len > 1 && str[0] == '"' && str[len - 1] == '"') {
        memmove(str, str + 1, len - 2);
        str[len - 2] = '\0';
    }
}

void organize_files(const char* dir_path, const char* save_path) {
    WIN32_FIND_DATA find_data;
    HANDLE hFind;
    char search_path[MAX_PATH];
    snprintf(search_path, MAX_PATH, "%s\\*", dir_path);
    
    hFind = FindFirstFile(search_path, &find_data);
    if (hFind == INVALID_HANDLE_VALUE) {
        printf("No files found.\n");
        return;
    }
    
    char base_path[MAX_PATH];
    snprintf(base_path, MAX_PATH, "%s", save_path[0] ? save_path : dir_path);
    
    char other_folders[MAX_PATH];
    snprintf(other_folders, MAX_PATH, "%s\\Other Folders", base_path);
    create_directory(other_folders);
    
    do {
        char file_path[MAX_PATH];
        snprintf(file_path, MAX_PATH, "%s\\%s", dir_path, find_data.cFileName);
        
        if (find_data.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) {
            if (strcmp(find_data.cFileName, ".") != 0 && strcmp(find_data.cFileName, "..") != 0) {
                move_file(file_path, other_folders, find_data.cFileName);
            }
        } else {
            FILETIME ftCreate = find_data.ftCreationTime;
            SYSTEMTIME stUTC, stLocal;
            FileTimeToSystemTime(&ftCreate, &stUTC);
            SystemTimeToTzSpecificLocalTime(NULL, &stUTC, &stLocal);
            
            char month_year[20];
            snprintf(month_year, 20, "%s %d", (char*[]) {"January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"}[stLocal.wMonth - 1], stLocal.wYear);
            
            char folder_path[MAX_PATH];
            snprintf(folder_path, MAX_PATH, "%s\\%s", base_path, month_year);
            create_directory(folder_path);
            
            char* ext = strrchr(find_data.cFileName, '.');
            if (ext) {
                ext++;
                char type_folder[MAX_PATH];
                snprintf(type_folder, MAX_PATH, "%s\\%s", folder_path, ext);
                create_directory(type_folder);
                move_file(file_path, type_folder, find_data.cFileName);
            } else {
                move_file(file_path, folder_path, find_data.cFileName);
            }
        }
    } while (FindNextFile(hFind, &find_data));
    
    FindClose(hFind);
}

int main() {
    char folder[MAX_PATH], save_folder[MAX_PATH] = "";
    char choice;
    
    printf("Enter the path of the directory to organize: ");
    gets(folder);
    remove_quotes(folder);
    
    printf("Do you want to save the sorted files in a different folder? (Y/N): ");
    scanf(" %c", &choice);
    getchar();
    
    if (choice == 'Y' || choice == 'y') {
        printf("Enter the path of the destination folder: ");
        gets(save_folder);
        remove_quotes(save_folder);
        create_directory(save_folder);
    }
    
    organize_files(folder, save_folder);
    
    printf("Files organized successfully. You can now exit the command prompt.\n");
    return 0;
}
