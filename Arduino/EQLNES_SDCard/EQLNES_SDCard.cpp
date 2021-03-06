#include <EQLNES_SDCard.h>
#include <Arduino.h>
#include <SdFat.h>
#include <String.h>

void EQLNES_SDCard::begin()
{
    _sd.begin(_csPin, SPI_FULL_SPEED);
}

bool EQLNES_SDCard::writeFile(char *filename, char *data)
{
    if (_file.open(filename, O_RDWR | O_CREAT | O_AT_END))
    {
        _file.println(data);
        _file.close();
        return true;
    }
    else
    {
        return false;
    }
}


bool EQLNES_SDCard::writeFile(char *filename, String data)
{
    if (_file.open(filename, O_RDWR | O_CREAT | O_AT_END))
    {
        _file.println(data);
        _file.close();
        return true;
    }
    else
    {
        return false;
    }
}

String EQLNES_SDCard::readFile(char *filename)
{
    char c;
    String buffer = "";
    if (_file.open(filename, O_READ))
    {
        while (_file.available())
        {
            c = _file.read();
            buffer += c;
        }
        _file.close();
    }
    return buffer;
}