#include <windows.h>
#include <shlobj.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#include <dirent.h>
#include <sys/stat.h>
#include <time.h>
#include <commctrl.h>
#include <shlwapi.h>
#include <wincrypt.h>

#pragma comment(lib, "shlwapi.lib")
#pragma comment(lib, "crypt32.lib")

#define MAX_PATH_LEN 260
#define MAX_CATEGORIES 20
#define MAX_EXTENSIONS_PER_CATEGORY 20
#define MAX_EXTENSION_LEN 10
#define MAX_CATEGORY_NAME_LEN 50
#define MAX_HISTORY_ENTRIES 100
#define ID_BROWSE 101
#define ID_SORT_TYPE 102
#define ID_SORT_ALPHA 103
#define ID_SORT_DATE 104
#define ID_SORT_SMART 105
#define ID_ANALYZE 106
#define ID_UNDO 107
#define ID_SETTINGS 108

// Helper function to replace _wctime_s
wchar_t* timeToWStr(const time_t* time, wchar_t* buf, size_t size) {
    if (time == NULL || buf == NULL || size < 26) return NULL;
    
    struct tm* tm_info = localtime(time);
    if (tm_info == NULL) return NULL;
    
    wchar_t temp[26];
    if (wcsftime(temp, sizeof(temp)/sizeof(wchar_t), L"%a %b %d %H:%M:%S %Y", tm_info) == 0)
        return NULL;
    
    wcscpy(buf, temp);
    return buf;
}

typedef struct {
    wchar_t originalPath[MAX_PATH_LEN];
    wchar_t newPath[MAX_PATH_LEN];
    time_t timestamp;
} FileAction;

typedef struct {
    wchar_t name[MAX_CATEGORY_NAME_LEN];
    wchar_t extensions[MAX_EXTENSIONS_PER_CATEGORY][MAX_EXTENSION_LEN];
    int extensionCount;
} FileCategory;

// Global variables
HWND hEdit, hStatus, hProgress;
wchar_t directoryPath[MAX_PATH_LEN] = {0};
FileAction actionHistory[MAX_HISTORY_ENTRIES];
int historyCount = 0;
BOOL isOrganizing = FALSE;
FileCategory categories[MAX_CATEGORIES];
int categoryCount = 0;

// Function prototypes
void InitializeCategories();
void sortByFileType(const wchar_t *directory);
void sortAlphabetically(const wchar_t *directory);
void sortByDate(const wchar_t *directory);
void smartOrganize(const wchar_t *directory);
void analyzeFiles(const wchar_t *directory);
void undoLastAction();
BOOL moveFile(const wchar_t *filePath, const wchar_t *newFolder, const wchar_t *fileName);
BOOL calculateFileHash(const wchar_t* filePath, wchar_t* hashResult);
void detectFileCategory(const wchar_t* fileExtension, wchar_t* category);
void findDuplicates(const wchar_t* directory);
void applyCustomRules(const wchar_t* directory);
LRESULT CALLBACK WindowProcedure(HWND, UINT, WPARAM, LPARAM);
void organizeOnSchedule(const wchar_t* directory, int daysInterval);

// Initialize file categories
void InitializeCategories() {
    categoryCount = 8; // Number of categories we'll define
    
    // Documents
    wcscpy_s(categories[0].name, MAX_CATEGORY_NAME_LEN, L"Documents");
    wcscpy_s(categories[0].extensions[0], MAX_EXTENSION_LEN, L".doc");
    wcscpy_s(categories[0].extensions[1], MAX_EXTENSION_LEN, L".docx");
    wcscpy_s(categories[0].extensions[2], MAX_EXTENSION_LEN, L".txt");
    wcscpy_s(categories[0].extensions[3], MAX_EXTENSION_LEN, L".pdf");
    categories[0].extensionCount = 4;

    // Images
    wcscpy_s(categories[1].name, MAX_CATEGORY_NAME_LEN, L"Images");
    wcscpy_s(categories[1].extensions[0], MAX_EXTENSION_LEN, L".jpg");
    wcscpy_s(categories[1].extensions[1], MAX_EXTENSION_LEN, L".jpeg");
    wcscpy_s(categories[1].extensions[2], MAX_EXTENSION_LEN, L".png");
    wcscpy_s(categories[1].extensions[3], MAX_EXTENSION_LEN, L".gif");
    categories[1].extensionCount = 4;

    // Videos
    wcscpy_s(categories[2].name, MAX_CATEGORY_NAME_LEN, L"Videos");
    wcscpy_s(categories[2].extensions[0], MAX_EXTENSION_LEN, L".mp4");
    wcscpy_s(categories[2].extensions[1], MAX_EXTENSION_LEN, L".avi");
    wcscpy_s(categories[2].extensions[2], MAX_EXTENSION_LEN, L".mov");
    categories[2].extensionCount = 3;

    // Music
    wcscpy_s(categories[3].name, MAX_CATEGORY_NAME_LEN, L"Music");
    wcscpy_s(categories[3].extensions[0], MAX_EXTENSION_LEN, L".mp3");
    wcscpy_s(categories[3].extensions[1], MAX_EXTENSION_LEN, L".wav");
    wcscpy_s(categories[3].extensions[2], MAX_EXTENSION_LEN, L".flac");
    categories[3].extensionCount = 3;

    // Archives
    wcscpy_s(categories[4].name, MAX_CATEGORY_NAME_LEN, L"Archives");
    wcscpy_s(categories[4].extensions[0], MAX_EXTENSION_LEN, L".zip");
    wcscpy_s(categories[4].extensions[1], MAX_EXTENSION_LEN, L".rar");
    wcscpy_s(categories[4].extensions[2], MAX_EXTENSION_LEN, L".7z");
    categories[4].extensionCount = 3;

    // Executables
    wcscpy_s(categories[5].name, MAX_CATEGORY_NAME_LEN, L"Executables");
    wcscpy_s(categories[5].extensions[0], MAX_EXTENSION_LEN, L".exe");
    wcscpy_s(categories[5].extensions[1], MAX_EXTENSION_LEN, L".msi");
    wcscpy_s(categories[5].extensions[2], MAX_EXTENSION_LEN, L".bat");
    categories[5].extensionCount = 3;

    // Code
    wcscpy_s(categories[6].name, MAX_CATEGORY_NAME_LEN, L"Code");
    wcscpy_s(categories[6].extensions[0], MAX_EXTENSION_LEN, L".c");
    wcscpy_s(categories[6].extensions[1], MAX_EXTENSION_LEN, L".cpp");
    wcscpy_s(categories[6].extensions[2], MAX_EXTENSION_LEN, L".h");
    wcscpy_s(categories[6].extensions[3], MAX_EXTENSION_LEN, L".java");
    categories[6].extensionCount = 4;

    // Spreadsheets
    wcscpy_s(categories[7].name, MAX_CATEGORY_NAME_LEN, L"Spreadsheets");
    wcscpy_s(categories[7].extensions[0], MAX_EXTENSION_LEN, L".xls");
    wcscpy_s(categories[7].extensions[1], MAX_EXTENSION_LEN, L".xlsx");
    wcscpy_s(categories[7].extensions[2], MAX_EXTENSION_LEN, L".csv");
    categories[7].extensionCount = 3;
}

// Calculate file hash for duplicate detection
BOOL calculateFileHash(const wchar_t* filePath, wchar_t* hashResult) {
    const int BUFFER_SIZE = 1024 * 1024; // 1MB buffer
    BYTE buffer[BUFFER_SIZE];
    DWORD bytesRead = 0;
    HCRYPTPROV hProv = 0;
    HCRYPTHASH hHash = 0;
    BYTE rgbHash[16];
    DWORD cbHash = 0;
    const wchar_t rgbDigits[] = L"0123456789abcdef";
    
    HANDLE hFile = CreateFileW(filePath, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_FLAG_SEQUENTIAL_SCAN, NULL);
    if (hFile == INVALID_HANDLE_VALUE) return FALSE;

    if (!CryptAcquireContext(&hProv, NULL, NULL, PROV_RSA_FULL, CRYPT_VERIFYCONTEXT)) {
        CloseHandle(hFile);
        return FALSE;
    }

    if (!CryptCreateHash(hProv, CALG_MD5, 0, 0, &hHash)) {
        CryptReleaseContext(hProv, 0);
        CloseHandle(hFile);
        return FALSE;
    }

    while (ReadFile(hFile, buffer, BUFFER_SIZE, &bytesRead, NULL)) {
        if (bytesRead == 0) break;
        if (!CryptHashData(hHash, buffer, bytesRead, 0)) {
            CryptReleaseContext(hProv, 0);
            CryptDestroyHash(hHash);
            CloseHandle(hFile);
            return FALSE;
        }
    }

    cbHash = 16;
    if (CryptGetHashParam(hHash, HP_HASHVAL, rgbHash, &cbHash, 0)) {
        for (DWORD i = 0; i < cbHash; i++) {
            hashResult[i*2] = rgbDigits[rgbHash[i] >> 4];
            hashResult[i*2+1] = rgbDigits[rgbHash[i] & 0xf];
        }
        hashResult[cbHash*2] = L'\0';
    }

    CryptDestroyHash(hHash);
    CryptReleaseContext(hProv, 0);
    CloseHandle(hFile);
    return TRUE;
}

// Detect file category based on extension
void detectFileCategory(const wchar_t* fileExtension, wchar_t* category) {
    wchar_t lowerExt[MAX_EXTENSION_LEN];
    wcscpy_s(lowerExt, MAX_EXTENSION_LEN, fileExtension);
    _wcslwr_s(lowerExt, MAX_EXTENSION_LEN);

    for (int i = 0; i < categoryCount; i++) {
        for (int j = 0; j < categories[i].extensionCount; j++) {
            if (wcscmp(lowerExt, categories[i].extensions[j]) == 0) {
                wcscpy_s(category, MAX_CATEGORY_NAME_LEN, categories[i].name);
                return;
            }
        }
    }
    
    // Default category for unknown types
    wcscpy_s(category, MAX_CATEGORY_NAME_LEN, L"Other");
}

// Move file with history tracking
BOOL moveFile(const wchar_t *filePath, const wchar_t *newFolder, const wchar_t *fileName) {
    wchar_t newFolderPath[MAX_PATH_LEN];
    wchar_t newFilePath[MAX_PATH_LEN];

    swprintf_s(newFolderPath, MAX_PATH_LEN, L"%s", newFolder);
    CreateDirectoryW(newFolderPath, NULL);

    swprintf_s(newFilePath, MAX_PATH_LEN, L"%s\\%s", newFolderPath, fileName);

    // Add to action history before moving
    if (historyCount < MAX_HISTORY_ENTRIES) {
        wcscpy_s(actionHistory[historyCount].originalPath, MAX_PATH_LEN, filePath);
        wcscpy_s(actionHistory[historyCount].newPath, MAX_PATH_LEN, newFilePath);
        actionHistory[historyCount].timestamp = time(NULL);
        historyCount++;
    }

    if (!MoveFileW(filePath, newFilePath)) {
        DWORD err = GetLastError();
        if (err == ERROR_ALREADY_EXISTS) {
            // Handle duplicate file names
            wchar_t uniqueName[MAX_PATH_LEN];
            wchar_t nameWithoutExt[MAX_PATH_LEN];
            wchar_t ext[MAX_EXTENSION_LEN];
            
            _wsplitpath_s(fileName, NULL, 0, NULL, 0, nameWithoutExt, MAX_PATH_LEN, ext, MAX_EXTENSION_LEN);
            
            int counter = 1;
            do {
                swprintf_s(uniqueName, MAX_PATH_LEN, L"%s (%d)%s", nameWithoutExt, counter, ext);
                swprintf_s(newFilePath, MAX_PATH_LEN, L"%s\\%s", newFolderPath, uniqueName);
                counter++;
            } while (PathFileExistsW(newFilePath));
            
            // Update action history with the new path
            wcscpy_s(actionHistory[historyCount-1].newPath, MAX_PATH_LEN, newFilePath);
            return MoveFileW(filePath, newFilePath);
        } else {
            fwprintf(stderr, L"Failed to move file: %s (Error: %d)\n", filePath, err);
            if (historyCount > 0) historyCount--; // Remove failed action from history
            return FALSE;
        }
    }
    return TRUE;
}

// Smart organization with categorization
void smartOrganize(const wchar_t *directory) {
    WIN32_FIND_DATAW findData;
    wchar_t searchPath[MAX_PATH_LEN];
    swprintf_s(searchPath, MAX_PATH_LEN, L"%s\\*", directory);

    HANDLE hFind = FindFirstFileW(searchPath, &findData);
    if (hFind == INVALID_HANDLE_VALUE) return;

    do {
        if (!(findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
            wchar_t filePath[MAX_PATH_LEN];
            swprintf_s(filePath, MAX_PATH_LEN, L"%s\\%s", directory, findData.cFileName);

            // Get file extension
            wchar_t ext[MAX_EXTENSION_LEN];
            _wsplitpath_s(findData.cFileName, NULL, 0, NULL, 0, NULL, 0, ext, MAX_EXTENSION_LEN);
            
            // Detect category
            wchar_t category[MAX_CATEGORY_NAME_LEN];
            detectFileCategory(ext, category);
            
            // Create destination folder
            wchar_t newFolder[MAX_PATH_LEN];
            swprintf_s(newFolder, MAX_PATH_LEN, L"%s\\%s", directory, category);
            
            // Move file to categorized folder
            moveFile(filePath, newFolder, findData.cFileName);
        }
    } while (FindNextFileW(hFind, &findData));
    FindClose(hFind);
    
    // Find duplicates after organization
    findDuplicates(directory);
}

// Find duplicate files
void findDuplicates(const wchar_t* directory) {
    typedef struct {
        wchar_t hash[33]; // 32 chars for MD5 + null terminator
        wchar_t paths[MAX_HISTORY_ENTRIES][MAX_PATH_LEN];
        int pathCount;
    } FileHashEntry;

    FileHashEntry* fileHashes = NULL;
    int hashCount = 0;
    int capacity = 0;
    
    WIN32_FIND_DATAW findData;
    wchar_t searchPath[MAX_PATH_LEN];
    swprintf_s(searchPath, MAX_PATH_LEN, L"%s\\*", directory);

    HANDLE hFind = FindFirstFileW(searchPath, &findData);
    if (hFind == INVALID_HANDLE_VALUE) return;

    do {
        if (!(findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
            wchar_t filePath[MAX_PATH_LEN];
            swprintf_s(filePath, MAX_PATH_LEN, L"%s\\%s", directory, findData.cFileName);

            wchar_t fileHash[33];
            if (calculateFileHash(filePath, fileHash)) {
                // Check if we already have this hash
                BOOL found = FALSE;
                for (int i = 0; i < hashCount; i++) {
                    if (wcscmp(fileHashes[i].hash, fileHash) == 0) {
                        if (fileHashes[i].pathCount < MAX_HISTORY_ENTRIES) {
                            wcscpy_s(fileHashes[i].paths[fileHashes[i].pathCount], MAX_PATH_LEN, filePath);
                            fileHashes[i].pathCount++;
                        }
                        found = TRUE;
                        break;
                    }
                }
                
                if (!found) {
                    // Resize array if needed
                    if (hashCount >= capacity) {
                        capacity = capacity == 0 ? 16 : capacity * 2;
                        FileHashEntry* newArray = (FileHashEntry*)realloc(fileHashes, capacity * sizeof(FileHashEntry));
                        if (!newArray) {
                            fwprintf(stderr, L"Memory allocation failed\n");
                            break;
                        }
                        fileHashes = newArray;
                    }
                    
                    // Add new entry
                    wcscpy_s(fileHashes[hashCount].hash, 33, fileHash);
                    wcscpy_s(fileHashes[hashCount].paths[0], MAX_PATH_LEN, filePath);
                    fileHashes[hashCount].pathCount = 1;
                    hashCount++;
                }
            }
        }
    } while (FindNextFileW(hFind, &findData));
    FindClose(hFind);

    // Process duplicates
    for (int i = 0; i < hashCount; i++) {
        if (fileHashes[i].pathCount > 1) {
            // Found duplicates - move to a "Duplicates" folder
            wchar_t dupFolder[MAX_PATH_LEN];
            swprintf_s(dupFolder, MAX_PATH_LEN, L"%s\\Duplicates", directory);
            CreateDirectoryW(dupFolder, NULL);

            // Keep the first file, move the rest to duplicates folder
            for (int j = 1; j < fileHashes[i].pathCount; j++) {
                wchar_t fileName[MAX_PATH_LEN];
                _wsplitpath_s(fileHashes[i].paths[j], NULL, 0, NULL, 0, fileName, MAX_PATH_LEN, NULL, 0);
                wcscat_s(fileName, MAX_PATH_LEN, PathFindExtensionW(fileHashes[i].paths[j]));
                moveFile(fileHashes[i].paths[j], dupFolder, fileName);
            }
        }
    }

    free(fileHashes);
}

// File analysis function
void analyzeFiles(const wchar_t* directory) {
    typedef struct {
        wchar_t ext[MAX_EXTENSION_LEN];
        int count;
        long long totalSize;
    } FileTypeInfo;

    FileTypeInfo* fileTypes = NULL;
    int typeCount = 0;
    int typeCapacity = 0;
    long long totalSize = 0;
    int fileCount = 0;
    int folderCount = 0;
    time_t oldestFile = 0;
    time_t newestFile = 0;

    WIN32_FIND_DATAW findData;
    wchar_t searchPath[MAX_PATH_LEN];
    swprintf_s(searchPath, MAX_PATH_LEN, L"%s\\*", directory);

    HANDLE hFind = FindFirstFileW(searchPath, &findData);
    if (hFind == INVALID_HANDLE_VALUE) return;

    do {
        if (wcscmp(findData.cFileName, L".") == 0 || wcscmp(findData.cFileName, L"..") == 0) {
            continue;
        }

        if (findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) {
            folderCount++;
        } else {
            fileCount++;
            
            // Get file extension
            wchar_t ext[MAX_EXTENSION_LEN];
            _wsplitpath_s(findData.cFileName, NULL, 0, NULL, 0, NULL, 0, ext, MAX_EXTENSION_LEN);
            
            // Calculate file size
            LARGE_INTEGER fileSize;
            fileSize.LowPart = findData.nFileSizeLow;
            fileSize.HighPart = findData.nFileSizeHigh;
            totalSize += fileSize.QuadPart;

            // Track file types
            BOOL found = FALSE;
            for (int i = 0; i < typeCount; i++) {
                if (wcscmp(fileTypes[i].ext, ext) == 0) {
                    fileTypes[i].count++;
                    fileTypes[i].totalSize += fileSize.QuadPart;
                    found = TRUE;
                    break;
                }
            }
            
            if (!found) {
                // Resize array if needed
                if (typeCount >= typeCapacity) {
                    typeCapacity = typeCapacity == 0 ? 16 : typeCapacity * 2;
                    FileTypeInfo* newArray = (FileTypeInfo*)realloc(fileTypes, typeCapacity * sizeof(FileTypeInfo));
                    if (!newArray) {
                        fwprintf(stderr, L"Memory allocation failed\n");
                        break;
                    }
                    fileTypes = newArray;
                }
                
                // Add new type
                wcscpy_s(fileTypes[typeCount].ext, MAX_EXTENSION_LEN, ext);
                fileTypes[typeCount].count = 1;
                fileTypes[typeCount].totalSize = fileSize.QuadPart;
                typeCount++;
            }

            // Get file times
            FILETIME ft = findData.ftLastWriteTime;
            ULARGE_INTEGER ull;
            ull.LowPart = ft.dwLowDateTime;
            ull.HighPart = ft.dwHighDateTime;
            time_t fileTime = ull.QuadPart / 10000000ULL - 11644473600ULL;

            if (oldestFile == 0 || fileTime < oldestFile) {
                oldestFile = fileTime;
            }
            if (newestFile == 0 || fileTime > newestFile) {
                newestFile = fileTime;
            }
        }
    } while (FindNextFileW(hFind, &findData));
    FindClose(hFind);

    // Prepare analysis results
    wchar_t analysisResult[4096];
    wchar_t temp[256];
    
    swprintf_s(analysisResult, 4096, L"File Analysis Results:\n");
    swprintf_s(temp, 256, L"Total files: %d\n", fileCount);
    wcscat_s(analysisResult, 4096, temp);
    swprintf_s(temp, 256, L"Total folders: %d\n", folderCount);
    wcscat_s(analysisResult, 4096, temp);
    swprintf_s(temp, 256, L"Total size: %.2f MB\n\n", (double)totalSize / (1024 * 1024));
    wcscat_s(analysisResult, 4096, temp);
    wcscat_s(analysisResult, 4096, L"File types:\n");

    for (int i = 0; i < typeCount; i++) {
        swprintf_s(temp, 256, L"%s: %d files (%.2f MB)\n", 
                  fileTypes[i].ext, 
                  fileTypes[i].count, 
                  (double)fileTypes[i].totalSize / (1024 * 1024));
        wcscat_s(analysisResult, 4096, temp);
    }

    // Convert time_t to readable format
    if (oldestFile != 0) {
        wchar_t timeStr[26];
        timeToWStr(&oldestFile, timeStr, 26);
        swprintf_s(temp, 256, L"\nOldest file: %s", timeStr);
        wcscat_s(analysisResult, 4096, temp);
    }
    if (newestFile != 0) {
        wchar_t timeStr[26];
        timeToWStr(&newestFile, timeStr, 26);
        swprintf_s(temp, 256, L"Newest file: %s", timeStr);
        wcscat_s(analysisResult, 4096, temp);
    }

    MessageBoxW(NULL, analysisResult, L"Analysis Results", MB_OK | MB_ICONINFORMATION);
    free(fileTypes);
}

// Undo functionality
void undoLastAction() {
    if (historyCount == 0) {
        MessageBoxW(NULL, L"No actions to undo", L"Info", MB_OK | MB_ICONINFORMATION);
        return;
    }

    const FileAction* lastAction = &actionHistory[historyCount-1];
    
    // Check if the file still exists at the new location
    if (PathFileExistsW(lastAction->newPath)) {
        // Move it back to the original location
        if (MoveFileW(lastAction->newPath, lastAction->originalPath)) {
            historyCount--;
            MessageBoxW(NULL, L"Undo successful", L"Success", MB_OK | MB_ICONINFORMATION);
        } else {
            MessageBoxW(NULL, L"Failed to undo the last action", L"Error", MB_OK | MB_ICONERROR);
        }
    } else {
        historyCount--;
        MessageBoxW(NULL, L"The file no longer exists at the target location", L"Info", MB_OK | MB_ICONINFORMATION);
    }
}

// Original sorting functions (modified for C)
void sortByFileType(const wchar_t *directory) {
    WIN32_FIND_DATAW findData;
    wchar_t searchPath[MAX_PATH_LEN];
    swprintf_s(searchPath, MAX_PATH_LEN, L"%s\\*", directory);

    HANDLE hFind = FindFirstFileW(searchPath, &findData);
    if (hFind == INVALID_HANDLE_VALUE) return;

    do {
        if (!(findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
            wchar_t *dot = wcsrchr(findData.cFileName, L'.');
            if (dot) {
                wchar_t filePath[MAX_PATH_LEN];
                wchar_t newFolder[MAX_PATH_LEN];
                swprintf_s(filePath, MAX_PATH_LEN, L"%s\\%s", directory, findData.cFileName);
                swprintf_s(newFolder, MAX_PATH_LEN, L"%s\\%s_Files", directory, dot + 1);
                moveFile(filePath, newFolder, findData.cFileName);
            }
        }
    } while (FindNextFileW(hFind, &findData));
    FindClose(hFind);
}

void sortAlphabetically(const wchar_t *directory) {
    WIN32_FIND_DATAW findData;
    wchar_t searchPath[MAX_PATH_LEN];
    swprintf_s(searchPath, MAX_PATH_LEN, L"%s\\*", directory);

    HANDLE hFind = FindFirstFileW(searchPath, &findData);
    if (hFind == INVALID_HANDLE_VALUE) return;

    wchar_t newFolder[MAX_PATH_LEN];
    swprintf_s(newFolder, MAX_PATH_LEN, L"%s\\Alphabetical", directory);
    CreateDirectoryW(newFolder, NULL);

    do {
        if (!(findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
            wchar_t filePath[MAX_PATH_LEN];
            swprintf_s(filePath, MAX_PATH_LEN, L"%s\\%s", directory, findData.cFileName);
            moveFile(filePath, newFolder, findData.cFileName);
        }
    } while (FindNextFileW(hFind, &findData));
    FindClose(hFind);
}

void sortByDate(const wchar_t *directory) {
    WIN32_FIND_DATAW findData;
    wchar_t searchPath[MAX_PATH_LEN];
    swprintf_s(searchPath, MAX_PATH_LEN, L"%s\\*", directory);

    HANDLE hFind = FindFirstFileW(searchPath, &findData);
    if (hFind == INVALID_HANDLE_VALUE) return;

    do {
        if (!(findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
            FILETIME ft = findData.ftCreationTime;
            SYSTEMTIME stUTC;
            FileTimeToSystemTime(&ft, &stUTC);

            wchar_t filePath[MAX_PATH_LEN];
            swprintf_s(filePath, MAX_PATH_LEN, L"%s\\%s", directory, findData.cFileName); 

            wchar_t dateFolder[MAX_PATH_LEN];
            swprintf_s(dateFolder, MAX_PATH_LEN, L"%s\\%04d-%02d", directory, stUTC.wYear, stUTC.wMonth);

            moveFile(filePath, dateFolder, findData.cFileName);
        }
    } while (FindNextFileW(hFind, &findData));
    FindClose(hFind);
}

// Window procedure
LRESULT CALLBACK WindowProcedure(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
    switch (msg) {
        case WM_CREATE: {
            InitializeCategories();
            
            CreateWindowW(L"Static", L"Directory Path:",
                          WS_VISIBLE | WS_CHILD,
                          20, 20, 100, 20, hwnd, NULL, NULL, NULL);

            hEdit = CreateWindowW(L"Edit", L"",
                                  WS_VISIBLE | WS_CHILD | WS_BORDER | ES_AUTOHSCROLL,
                                  130, 20, 250, 20, hwnd, NULL, NULL, NULL);

            CreateWindowW(L"Button", L"Browse",
                          WS_VISIBLE | WS_CHILD,
                          390, 20, 80, 20, hwnd, (HMENU)ID_BROWSE, NULL, NULL);

            // Organization buttons
            CreateWindowW(L"Button", L"Sort by File Type",
                          WS_VISIBLE | WS_CHILD,
                          20, 60, 150, 30, hwnd, (HMENU)ID_SORT_TYPE, NULL, NULL);

            CreateWindowW(L"Button", L"Sort Alphabetically",
                          WS_VISIBLE | WS_CHILD,
                          180, 60, 150, 30, hwnd, (HMENU)ID_SORT_ALPHA, NULL, NULL);

            CreateWindowW(L"Button", L"Sort by Date",
                          WS_VISIBLE | WS_CHILD,
                          340, 60, 150, 30, hwnd, (HMENU)ID_SORT_DATE, NULL, NULL);
            //initiliaze progree bar 
            hProgress = CreateWindowW(PROGRESS_CLASSW, NULL,
                            WS_VISIBLE | WS_CHILD | PBS_SMOOTH,
                            20, 180, 450, 20, hwnd, NULL, NULL, NULL);
                        SendMessage(hProgress, PBM_SETRANGE, 0, MAKELPARAM(0, 100));
                        SendMessage(hProgress, PBM_SETSTEP, 1, 0);
            // New features buttons
            CreateWindowW(L"Button", L"Smart Organize",
                          WS_VISIBLE | WS_CHILD,
                          20, 100, 150, 30, hwnd, (HMENU)ID_SORT_SMART, NULL, NULL);

            CreateWindowW(L"Button", L"Analyze Files",
                          WS_VISIBLE | WS_CHILD,
                          180, 100, 150, 30, hwnd, (HMENU)ID_ANALYZE, NULL, NULL);

            CreateWindowW(L"Button", L"Undo Last Action",
                          WS_VISIBLE | WS_CHILD,
                          340, 100, 150, 30, hwnd, (HMENU)ID_UNDO, NULL, NULL);

            CreateWindowW(L"Button", L"Settings",
                          WS_VISIBLE | WS_CHILD,
                          20, 140, 150, 30, hwnd, (HMENU)ID_SETTINGS, NULL, NULL);

            // Progress bar
            hProgress = CreateWindowW(PROGRESS_CLASSW, NULL,
                         WS_VISIBLE | WS_CHILD | PBS_SMOOTH,
                         20, 180, 450, 20, hwnd, NULL, NULL, NULL);

            // Status bar
            hStatus = CreateWindowW(STATUSCLASSNAMEW, L"Ready",
                                    WS_VISIBLE | WS_CHILD | SBARS_SIZEGRIP,
                                    0, 0, 0, 0, hwnd, NULL, NULL, NULL);
            break;
        }

        case WM_SIZE: {
            RECT rcClient;
            GetClientRect(hwnd, &rcClient);
            
            // Position the status bar
            SendMessage(hStatus, WM_SIZE, 0, 0);
            
            // Resize other controls as needed
            break;
        }

        case WM_COMMAND: {
            switch (LOWORD(wp)) {
                case ID_BROWSE: {
                    BROWSEINFOW bi = {0};
                    bi.hwndOwner = hwnd;
                    bi.lpszTitle = L"Select a folder";
                    bi.ulFlags = BIF_RETURNONLYFSDIRS | BIF_NEWDIALOGSTYLE;

                    LPITEMIDLIST pidl = SHBrowseForFolderW(&bi);
                    if (pidl != NULL) {
                        SHGetPathFromIDListW(pidl, directoryPath);
                        SetWindowTextW(hEdit, directoryPath);
                        CoTaskMemFree(pidl);
                    }
                    break;
                }

                case ID_SORT_TYPE:
                case ID_SORT_ALPHA:
                case ID_SORT_DATE:
                case ID_SORT_SMART:
                case ID_ANALYZE: {
                    if (isOrganizing) {
                        MessageBoxW(hwnd, L"Organization is already in progress", L"Info", MB_OK | MB_ICONINFORMATION);
                        break;
                    }

                    GetWindowTextW(hEdit, directoryPath, MAX_PATH_LEN);
                    if (wcslen(directoryPath) == 0) {
                        MessageBoxW(hwnd, L"Please select a directory first", L"Error", MB_ICONERROR);
                        break;
                    }

                    isOrganizing = TRUE;
                    SetWindowTextW(hStatus, L"Working...");
                    SendMessage(hProgress, PBM_SETMARQUEE, (WPARAM)TRUE, 0);

                    // Perform the requested operation
                    switch (LOWORD(wp)) {
                        case ID_SORT_TYPE:
                            sortByFileType(directoryPath);
                            break;
                        case ID_SORT_ALPHA:
                            sortAlphabetically(directoryPath);
                            break;
                        case ID_SORT_DATE:
                            sortByDate(directoryPath);
                            break;
                        case ID_SORT_SMART:
                            smartOrganize(directoryPath);
                            break;
                        case ID_ANALYZE:
                            analyzeFiles(directoryPath);
                            break;
                    }

                    isOrganizing = FALSE;
                    SetWindowTextW(hStatus, L"Ready");
                    SendMessage(hProgress, PBM_SETMARQUEE, (WPARAM)FALSE, 0);
                    SendMessage(hProgress, PBM_SETPOS, 0, 0); 
                    }
                    if (LOWORD(wp) != ID_ANALYZE) {
                    MessageBoxW(hwnd, L"Files have been organized successfully!", L"Success", MB_ICONINFORMATION);
                    }break;
            
                case ID_UNDO:
                    undoLastAction();
                    break;

                case ID_SETTINGS:
                    MessageBoxW(hwnd, L"Settings would be implemented here", L"Info", MB_OK | MB_ICONINFORMATION);
                    break;
            }
            break;
        }

        case WM_DESTROY:
            PostQuitMessage(0);
            break;

        default:
            return DefWindowProcW(hwnd, msg, wp, lp);
    }
    return 0;
}

int WINAPI WinMain(HINSTANCE hInst, HINSTANCE hPrevInst, LPSTR args, int ncmdshow) {
    INITCOMMONCONTROLSEX icex = {sizeof(INITCOMMONCONTROLSEX), ICC_WIN95_CLASSES};
    InitCommonControlsEx(&icex);

    WNDCLASSW wc = {0};
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.hInstance = hInst;
    wc.lpszClassName = L"FileOrganizerClass";
    wc.lpfnWndProc = WindowProcedure;

    if (!RegisterClassW(&wc)) return -1;

    HWND hwnd = CreateWindowW(L"FileOrganizerClass", L"File Organizer",
                              WS_OVERLAPPEDWINDOW | WS_VISIBLE,
                              100, 100, 600, 300, NULL, NULL, hInst, NULL);

    MSG msg = {0};
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    return 0;
}
