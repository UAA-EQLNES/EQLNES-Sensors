#ifndef _UASENSORS_SIM900_H_
#define _UASENSORS_SIM900_H_

#include <Arduino.h>
#include <String.h>

class UASensors_Sim900 {
public:
    void begin(Stream *serial);
    void togglePower();
    bool isReady(int timeout);
    void clearBuffer();
    void sendTextMsg(String msg, String phoneNumber);
    bool isTextMsgDelivered(int timeout);
    void writeAtCommand(String command);
    int read();
    int available();
private:
    Stream *_serial;
    int _powerPin;
};

#endif