#include <SPI.h>
#include <Bitcraze_PMW3901.h>
#include <MAVLink.h>

// =====================================================
// CJMCU3901 / PMW3901
// =====================================================

#define PMW3901_CS 10

Bitcraze_PMW3901 flow(PMW3901_CS);


// =====================================================
// MAVLink
// =====================================================

// Samakan dengan SYSID kendaraan/Pixhawk.
// Default ArduPilot biasanya 1.
#define MAV_SYS_ID 1

// Arduino merupakan peripheral MAVLink,
// bukan onboard computer.
//
// Raspberry Pi nantinya dapat menggunakan
// MAV_COMP_ID_ONBOARD_COMPUTER.
#define MAV_COMP_ID MAV_COMP_ID_PERIPHERAL

// ID sensor optical flow
#define FLOW_SENSOR_ID 0


// =====================================================
// Optical Flow Scale
// =====================================================

// Starting scale PMW3901.
// Belum final karena tetap harus divalidasi
// menggunakan hasil kalibrasi.
const float FLOW_SCALE_X = 1.351e-3f;
const float FLOW_SCALE_Y = 1.078e-3f;


// =====================================================
// Axis Sign
// =====================================================

// Berdasarkan konfigurasi/kalibrasi saat ini.
//
// X dibalik.
// Y tidak dibalik.
//
// Jangan diubah tanpa melihat hasil kalibrasi.
const float SIGN_X = -1.0f;
const float SIGN_Y = 1.0f;


// =====================================================
// Timing
// =====================================================

// 20 ms = 50 Hz
const uint32_t FLOW_PERIOD_US = 20000UL;

uint32_t lastFlowTime = 0;


// =====================================================
// Extended 64-bit Timestamp
// =====================================================

// micros() pada Arduino Nano berbasis AVR adalah uint32_t
// dan akan rollover sekitar setiap 71 menit.
//
// Fungsi ini memperpanjang micros() menjadi uint64_t
// sehingga timestamp MAVLink tetap monoton dalam
// penggunaan jangka panjang.
uint64_t micros64()
{
    static uint32_t previousMicros = 0;
    static uint64_t upperMicros = 0;

    uint32_t currentMicros = micros();

    // Detect rollover uint32_t
    if (currentMicros < previousMicros)
    {
        upperMicros += (1ULL << 32);
    }

    previousMicros = currentMicros;

    return upperMicros | (uint64_t)currentMicros;
}


// =====================================================
// Optical Flow Variables
// =====================================================

int16_t deltaX = 0;
int16_t deltaY = 0;

// SQUAL asli dari PMW3901
uint8_t flowQuality = 0;


// =====================================================
// Send MAVLink OPTICAL_FLOW
// =====================================================

void sendOpticalFlow(
    int16_t dx,
    int16_t dy,
    float flowRateX,
    float flowRateY,
    uint8_t quality
)
{
    mavlink_message_t msg;
    uint8_t buffer[MAVLINK_MAX_PACKET_LEN];

    // Timestamp 64-bit sejak Arduino boot.
    uint64_t timestampUs = micros64();

    mavlink_msg_optical_flow_pack(
        MAV_SYS_ID,          // system ID
        MAV_COMP_ID,         // component ID
        &msg,

        timestampUs,         // time_usec [us]

        FLOW_SENSOR_ID,      // sensor_id

        dx,                  // flow_x raw count
        dy,                  // flow_y raw count

        0.0f,                // flow_comp_m_x
        0.0f,                // flow_comp_m_y

        quality,             // SQUAL PMW3901

        -1.0f,               // ground_distance unknown

        flowRateX,           // flow_rate_x [rad/s]
        flowRateY            // flow_rate_y [rad/s]
    );

    uint16_t len =
        mavlink_msg_to_send_buffer(
            buffer,
            &msg
        );

    Serial.write(
        buffer,
        len
    );
}


// =====================================================
// Setup
// =====================================================

void setup()
{
    // =================================================
    // UART Arduino Nano -> Pixhawk TELEM2
    // =================================================
    //
    // Pixhawk TELEM2 harus menggunakan baud yang sama.
    //
    // Jangan menggunakan Serial.print()/println()
    // karena port ini membawa MAVLink binary.
    Serial.begin(115200);

    delay(1000);


    // =================================================
    // Initialize PMW3901
    // =================================================

    if (!flow.begin())
    {
        // Tidak menggunakan Serial.println()
        // karena Serial digunakan untuk MAVLink.

        while (1)
        {
            delay(1000);
        }
    }


    // =================================================
    // Initialize Timing
    // =================================================

    lastFlowTime = micros();
}


// =====================================================
// Main Loop
// =====================================================

void loop()
{
    uint32_t now = micros();


    // =================================================
    // Run Optical Flow at 50 Hz
    // =================================================

    if (
        (uint32_t)(now - lastFlowTime)
        >= FLOW_PERIOD_US
    )
    {
        uint32_t elapsed =
            now - lastFlowTime;

        lastFlowTime = now;


        // =============================================
        // Calculate dt
        // =============================================

        float dt =
            ((float)elapsed)
            * 1.0e-6f;


        // Safety protection.
        if (dt <= 0.0f)
        {
            return;
        }


        // =============================================
        // Reset Variables
        // =============================================

        deltaX = 0;
        deltaY = 0;
        flowQuality = 0;


        // =============================================
        // Read CJMCU3901 / PMW3901
        // =============================================

        flow.readMotionCount(
            &deltaX,
            &deltaY,
            &flowQuality
        );


        // =============================================
        // Convert Optical Flow
        //
        // count
        //   ↓
        // radians
        //   ↓
        // rad/s
        //
        // flowRate = count * scale / dt
        // =============================================

        float flowRateX =
            SIGN_X
            *
            ((float)deltaX * FLOW_SCALE_X)
            /
            dt;


        float flowRateY =
            SIGN_Y
            *
            ((float)deltaY * FLOW_SCALE_Y)
            /
            dt;


        // =============================================
        // Invalid Measurement Protection
        // =============================================
        //
        // Jika SQUAL = 0, measurement dianggap tidak
        // memiliki kualitas optical-flow yang valid.
        //
        // Raw count DAN rate dibuat 0 agar tidak ada
        // data gerakan yang ambigu dalam paket MAVLink.
        //
        // quality tetap dikirim sebagai 0 sehingga
        // Pixhawk mengetahui measurement buruk.
        // =============================================

        if (flowQuality == 0)
        {
            deltaX = 0;
            deltaY = 0;

            flowRateX = 0.0f;
            flowRateY = 0.0f;
        }


        // =============================================
        // Send MAVLink OPTICAL_FLOW
        // =============================================

        sendOpticalFlow(
            deltaX,
            deltaY,
            flowRateX,
            flowRateY,
            flowQuality
        );
    }
}
