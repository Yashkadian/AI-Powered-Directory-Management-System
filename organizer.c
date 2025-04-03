#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <sys/stat.h>
#include <time.h>

#define MAX_PATH 260

void sortByFileType(const char *directory);
void sortAlphabetically(const char *directory);
void sortByDate(const char *directory);
void moveFile(const char *filePath, const char *newFolder, const char *fileName);

int main() {

    char directory[MAX_PATH];

    // Get directory path from user
    printf("Enter directory path to organize: ");
    fgets(directory, sizeof(directory), stdin);
    directory[strcspn(directory, "\n")] = '\0'; 

    printf("Checking directory: %s\n", directory);
    DIR *dir = opendir(directory);
    if (dir == NULL) {
        perror("Error");
        return 1;
    }
    closedir(dir);

 
    int choice;
    printf("\nChoose sorting method:\n");
    printf("1. Sort by File Type\n");
    printf("2. Sort Alphabetically (A-Z)\n");
    printf("3. Sort by Date (YYYY-MM)\n");
    printf("Enter choice: ");

    if (scanf("%d", &choice) != 1) {
        while (getchar() != '\n'); 
        printf("Invalid choice! Please enter a number between 1 and 3.\n");
        return 1;
    }

    switch (choice) {
        case 1:
            sortByFileType(directory);
            break;
        case 2:
            sortAlphabetically(directory);
            break;
        case 3:
            sortByDate(directory);
            break;
        default:
            printf("Invalid choice! Please enter a number between 1 and 3.\n");
            return 1;
    }

    printf("\n✅ Files have been organized successfully!\n");
    return 0;
}
void moveFile(const char *filePath, const char *newFolder, const char *fileName) {
    char newFolderPath[MAX_PATH];
    char newFilePath[MAX_PATH];

    snprintf(newFolderPath, sizeof(newFolderPath), "%s/%s", newFolder, fileName);
    snprintf(newFilePath, sizeof(newFilePath), "%s/%s", newFolder, fileName);

    mkdir(newFolder); // Create folder if not exists

    if (rename(filePath, newFilePath) != 0) {
        perror("Error moving file");
    }
}

// Sort files by file type (extension)
void sortByFileType(const char *directory) {
    struct dirent *entry;
    DIR *dir = opendir(directory);

    if (dir == NULL) {
        perror("Error opening directory");
        return;
    }

    while ((entry = readdir(dir)) != NULL) {
        if (entry->d_type == DT_REG) {
            char *dot = strrchr(entry->d_name, '.');
            if (dot) {
                char filePath[MAX_PATH];
                char newFolder[MAX_PATH];

                snprintf(filePath, sizeof(filePath), "%s/%s", directory, entry->d_name);
                snprintf(newFolder, sizeof(newFolder), "%s/%s_Files", directory, dot + 1);

                moveFile(filePath, newFolder, entry->d_name);
            }
        }
    }
    closedir(dir);
}

// Sort files alphabetically (A-Z)
void sortAlphabetically(const char *directory) {
    struct dirent *entry;
    DIR *dir = opendir(directory);

    if (dir == NULL) {
        perror("Error opening directory");
        return;
    }

    char newFolder[MAX_PATH];
    snprintf(newFolder, sizeof(newFolder), "%s/Alphabetical", directory);
    mkdir(newFolder);

    while ((entry = readdir(dir)) != NULL) {
        if (entry->d_type == DT_REG) {
            char filePath[MAX_PATH];
            snprintf(filePath, sizeof(filePath), "%s/%s", directory, entry->d_name);
            moveFile(filePath, newFolder, entry->d_name);
        }
    }
    closedir(dir);
}

// Sort files by creation date (YYYY-MM)
void sortByDate(const char *directory) {
    struct dirent *entry;
    DIR *dir = opendir(directory);

    if (dir == NULL) {
        perror("Error opening directory");
        return;
    }

    struct stat fileStat;
    while ((entry = readdir(dir)) != NULL) {
        if (entry->d_type == DT_REG) {
            char filePath[MAX_PATH];
            snprintf(filePath, sizeof(filePath), "%s/%s", directory, entry->d_name);

            if (stat(filePath, &fileStat) == 0) {
                struct tm *timeInfo = localtime(&fileStat.st_ctime);
                char dateFolder[MAX_PATH];

                snprintf(dateFolder, sizeof(dateFolder), "%s/%04d-%02d", directory,
                         timeInfo->tm_year + 1900, timeInfo->tm_mon + 1);

                moveFile(filePath, dateFolder, entry->d_name);
            }
        }
    }
    closedir(dir);
}


