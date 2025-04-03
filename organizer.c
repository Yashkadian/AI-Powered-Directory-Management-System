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
