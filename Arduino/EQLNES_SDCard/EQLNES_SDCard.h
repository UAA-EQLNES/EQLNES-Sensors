#ifndef _EQLNES_SDCARD_H_
#define _EQLNES_SDCARD_H_

#include <Arduino.h>
#include <String.h>
#include <SdFat.h>

class EQLNES_SDCard {
public:
    EQLNES_SDCard(int csPin) : _csPin(csPin) {};
    void begin();
    bool writeFile(char *filename, char *data);
    bool writeFile(char *filename, String data);
    String readFile(char *filename);
private:
    SdFat _sd;
    SdFile _file;
    int _csPin;
};

#endif