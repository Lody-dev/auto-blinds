#include <Arduino.h>
#include <Bounce2.h>
#include <AccelStepper.h>
#include <WiFi.h>
#include <WebServer.h>

// --- Pin defines ---
#define DIR_PIN     12
#define STEP_PIN    14
#define ENABLE_PIN  26
#define B_UP        13
#define B_DOWN      4
#define B_ON        27
#define RELAY       33

// --- Stepper setup ---
AccelStepper stepper(AccelStepper::DRIVER, STEP_PIN, DIR_PIN);

// --- Globals ---
const char* ssid     = "PointerToWifi";
const char* password = "PzxdpDbc";
WebServer server(80);

unsigned long lastPrint = 0;
unsigned long limit = 5000;
int flag = 1;
bool isSetUp = false;
bool webControl = false;

// Button debouncers
Bounce button_up   = Bounce();
Bounce button_down = Bounce();

// --- Timers ---
static unsigned long moveUpStart   = 0;
static unsigned long moveDownStart = 0;
static unsigned long comboStart    = 0;

bool upPrev = false;
bool downPrev = false;

void setup() 
{
  // Pins
  pinMode(B_UP, INPUT_PULLUP);
  pinMode(B_DOWN, INPUT_PULLUP);
  pinMode(B_ON, INPUT_PULLUP);
  pinMode(DIR_PIN, OUTPUT);
  pinMode(STEP_PIN, OUTPUT);
  pinMode(ENABLE_PIN, OUTPUT);
  pinMode(RELAY, OUTPUT);

  Serial.begin(115200);
                        
  stepper.setMaxSpeed(1000);  
  stepper.setAcceleration(500);
  digitalWrite(RELAY, HIGH);
  digitalWrite(ENABLE_PIN, LOW);

  // Buttons
  button_up.attach(B_UP);
  button_up.interval(10);
  button_down.attach(B_DOWN);
  button_down.interval(10);

  //WIFI STuff
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) 
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected! IP: " + WiFi.localIP().toString());

  // HTTP routes
  server.on("/goto", handleGoto);
  server.on("/get_current_pos", handleCurrentPos);
  server.on("/get_max_pos", handleMaxPos);
  server.on("/get_set_up_status", handleSetUpStatus);
  server.begin();
  Serial.println("HTTP server started");
}

void handleGoto() 
{
  if (!server.hasArg("pos") || !isSetUp) 
  {
    server.send(400, "text/plain", "Missing pos param");
    return;
  }

  long target = server.arg("pos").toInt();
  target = constrain(target, 0, limit);
  Serial.println("got request");
  
  webControl = true;
  // --- Restore acceleration mode ---
  stepper.stop();                // cancel any constant-speed motion
  stepper.setAcceleration(500);  // restore accel (it’s lost after setSpeed)
  stepper.setCurrentPosition(stepper.currentPosition());
  stepper.moveTo(target);        // schedule target
  server.send(200, "text/plain", "Moving to position " + String(target));
}

void handleCurrentPos()
{
  server.send(200, "text/plain", String(stepper.currentPosition()));
}
void handleMaxPos()
{
  server.send(200, "text/plain", String(limit));
}
void handleSetUpStatus()
{
  server.send(200, "text/plain", String(isSetUp));
}

void loop() 
{
  server.handleClient();
  
  // --- Run stepper ---
  stepper.run();
  
  if (stepper.distanceToGo() == 0 && webControl)
  {
    Serial.println("Finished moving");
    webControl = false;
  }

  //Utils:
  // --- Update buttons ---
  button_up.update();
  button_down.update();
  bool up   = (button_up.read() == LOW);
  bool down = (button_down.read() == LOW);

  // --- Relay toggle ---
  if (digitalRead(B_ON) == LOW) 
  {
    flag = -flag;
    digitalWrite(RELAY, (flag == 1) ? HIGH : LOW);
    delay(600);
  }


  // --- Motor control ---
  if (!webControl)
  {
    if (up && !down && stepper.currentPosition() < limit) 
    {
      if (moveUpStart == 0) 
        moveUpStart = millis();
      if (millis() - moveUpStart >= 300) 
        stepper.setSpeed(600);
    }
    else if (down && !up && stepper.currentPosition() > 0) 
    {
      if (moveDownStart == 0) 
        moveDownStart = millis();
      if (millis() - moveDownStart >= 300) 
        stepper.setSpeed(-600);
    }
    else 
    {
      stepper.setSpeed(0);
      moveUpStart = 0;
      moveDownStart = 0;
    }

    //--- Combo press actions ---
    if (up && down) 
    {
      if (comboStart == 0) 
        comboStart = millis();
      unsigned long held = millis() - comboStart;

      if (!isSetUp && held == 500) 
      {
        limit = stepper.currentPosition();
        isSetUp = true;
        Serial.println("Limit set");
      }
      else if (isSetUp && held == 3000) 
      {
        limit = 5000;
        isSetUp = false;
        Serial.println("Reset");
      }
    } 
    else 
      comboStart = 0;  // reset combo timer when not both pressed
  }
}
