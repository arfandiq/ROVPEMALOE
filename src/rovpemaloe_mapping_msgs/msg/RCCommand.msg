# Vehicle RC inputs, NOT individual motor outputs. Pixhawk performs mixing.
std_msgs/Header header
uint16[6] channels # microseconds: roll, pitch, heave, yaw, forward, lateral
int8 arm_request # 0=no request, 1=arm, -1=disarm; edge event, never inferred state
