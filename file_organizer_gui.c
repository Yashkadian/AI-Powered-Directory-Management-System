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

#define MAX_PATH_LEN 260
#define ID_BROWSE 101
#define ID_SORT_TYPE 102
#define ID_SORT_ALPHA 103
#define ID_SORT_DATE 104

// Function prototypes
void sortByFileType(const wchar_t *directory);
void sortAlphabetically(const wchar_t *directory);
void sortByDate(const wchar_t *directory);
void moveFile(const wchar_t *filePath, const wchar_t *newFolder, const wchar_t *fileName);
LRESULT CALLBACK WindowProcedure(HWND, UINT, WPARAM, LPARAM);

// Global variables
HWND hEdit, hStatus;
wchar_t directoryPath[MAX_PATH_LEN] = {0};

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
                              100, 100, 500, 300, NULL, NULL, hInst, NULL);

    MSG msg = {0};
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    return 0;
}

LRESULT CALLBACK WindowProcedure(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
    switch (msg) {
        case WM_CREATE: {
            CreateWindowW(L"Static", L"Directory Path:",
                          WS_VISIBLE | WS_CHILD,
                          20, 20, 100, 20, hwnd, NULL, NULL, NULL);

            hEdit = CreateWindowW(L"Edit", L"",
                                  WS_VISIBLE | WS_CHILD | WS_BORDER | ES_AUTOHSCROLL,
                                  130, 20, 250, 20, hwnd, NULL, NULL, NULL);

            CreateWindowW(L"Button", L"Browse",
                          WS_VISIBLE | WS_CHILD,
                          390, 20, 80, 20, hwnd, (HMENU)ID_BROWSE, NULL, NULL);

            CreateWindowW(L"Button", L"Sort by File Type",
                          WS_VISIBLE | WS_CHILD,
                          130, 60, 150, 30, hwnd, (HMENU)ID_SORT_TYPE, NULL, NULL);

            CreateWindowW(L"Button", L"Sort Alphabetically",
                          WS_VISIBLE | WS_CHILD,
                          130, 100, 150, 30, hwnd, (HMENU)ID_SORT_ALPHA, NULL, NULL);

            CreateWindowW(L"Button", L"Sort by Date",
                          WS_VISIBLE | WS_CHILD,
                          130, 140, 150, 30, hwnd, (HMENU)ID_SORT_DATE, NULL, NULL);

            hStatus = CreateWindowW(STATUSCLASSNAMEW, L"Ready",
                                    WS_VISIBLE | WS_CHILD | SBARS_SIZEGRIP,
                                    0, 0, 0, 0, hwnd, NULL, NULL, NULL);
            break;
        }

        case WM_SIZE:
            SendMessage(hStatus, WM_SIZE, 0, 0);
            break;

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
                case ID_SORT_DATE: {
                    GetWindowTextW(hEdit, directoryPath, MAX_PATH_LEN);

                    WIN32_FIND_DATAW findData;
                    HANDLE hFind = FindFirstFileW(directoryPath, &findData);
                    if (hFind == INVALID_HANDLE_VALUE) {
                        MessageBoxW(hwnd, L"Invalid directory path!", L"Error", MB_ICONERROR);
                        break;
                    }
                    FindClose(hFind);

                    SetWindowTextW(hStatus, L"Organizing files...");

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
                    }

                    MessageBoxW(hwnd, L"Files have been organized successfully!", L"Success", MB_ICONINFORMATION);
                    SetWindowTextW(hStatus, L"Ready");
                    break;
                }
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

void moveFile(const wchar_t *filePath, const wchar_t *newFolder, const wchar_t *fileName) {
    wchar_t newFolderPath[MAX_PATH_LEN];
    wchar_t newFilePath[MAX_PATH_LEN];

    swprintf(newFolderPath, MAX_PATH_LEN, L"%s", newFolder);
    CreateDirectoryW(newFolderPath, NULL);

    swprintf(newFilePath, MAX_PATH_LEN, L"%s\\%s", newFolderPath, fileName);

    if (!MoveFileW(filePath, newFilePath)) {
        fwprintf(stderr, L"Failed to move file: %s\n", filePath);
    }
}

void sortByFileType(const wchar_t *directory) {
    WIN32_FIND_DATAW findData;
    wchar_t searchPath[MAX_PATH_LEN];
    swprintf(searchPath, MAX_PATH_LEN, L"%s\\*", directory);

    HANDLE hFind = FindFirstFileW(searchPath, &findData);
    if (hFind == INVALID_HANDLE_VALUE) return;

    do {
        if (!(findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
            wchar_t *dot = wcsrchr(findData.cFileName, L'.');
            if (dot) {
                wchar_t filePath[MAX_PATH_LEN];
                wchar_t newFolder[MAX_PATH_LEN];
                swprintf(filePath, MAX_PATH_LEN, L"%s\\%s", directory, findData.cFileName);
                swprintf(newFolder, MAX_PATH_LEN, L"%s\\%s_Files", directory, dot + 1);
                moveFile(filePath, newFolder, findData.cFileName);
            }
        }
    } while (FindNextFileW(hFind, &findData));
    FindClose(hFind);
}

void sortAlphabetically(const wchar_t *directory) {
    WIN32_FIND_DATAW findData;
    wchar_t searchPath[MAX_PATH_LEN];
    swprintf(searchPath, MAX_PATH_LEN, L"%s\\*", directory);

    HANDLE hFind = FindFirstFileW(searchPath, &findData);
    if (hFind == INVALID_HANDLE_VALUE) return;

    wchar_t newFolder[MAX_PATH_LEN];
    swprintf(newFolder, MAX_PATH_LEN, L"%s\\Alphabetical", directory);
    CreateDirectoryW(newFolder, NULL);

    do {
        if (!(findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
            wchar_t filePath[MAX_PATH_LEN];
            swprintf(filePath, MAX_PATH_LEN, L"%s\\%s", directory, findData.cFileName);
            moveFile(filePath, newFolder, findData.cFileName);
        }
    } while (FindNextFileW(hFind, &findData));
    FindClose(hFind);
}

void sortByDate(const wchar_t *directory) {
    WIN32_FIND_DATAW findData;
    wchar_t searchPath[MAX_PATH_LEN];
    swprintf(searchPath, MAX_PATH_LEN, L"%s\\*", directory);

    HANDLE hFind = FindFirstFileW(searchPath, &findData);
    if (hFind == INVALID_HANDLE_VALUE) return;

    do {
        if (!(findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
            FILETIME ft = findData.ftCreationTime;
            SYSTEMTIME stUTC;
            FileTimeToSystemTime(&ft, &stUTC);

            wchar_t filePath[MAX_PATH_LEN];
            swprintf(filePath, MAX_PATH_LEN, L"%s\\%s", directory, findData.cFileName);

            wchar_t dateFolder[MAX_PATH_LEN];
            swprintf(dateFolder, MAX_PATH_LEN, L"%s\\%04d-%02d", directory, stUTC.wYear, stUTC.wMonth);

            moveFile(filePath, dateFolder, findData.cFileName);
        }
    } while (FindNextFileW(hFind, &findData));
    FindClose(hFind);
}
