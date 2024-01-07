#!/usr/bin/env python

import rospy
from geometry_msgs.msg import PoseStamped
from mavros_msgs.msg import State
from mavros_msgs.srv import CommandBool, SetMode, CommandBoolRequest, SetModeRequest

current_state = State()

def state_cb(msg):
    global current_state
    current_state = msg

def offb_node():
    rospy.init_node('offb_node', anonymous=True)

    rospy.Subscriber('mavros/state', State, state_cb)
    local_pos_pub = rospy.Publisher('mavros/setpoint_position/local', PoseStamped, queue_size=10)
    arming_client = rospy.ServiceProxy('mavros/cmd/arming', CommandBool)
    set_mode_client = rospy.ServiceProxy('mavros/set_mode', SetMode)

    rate = rospy.Rate(20.0)  # 20 Hz

    # Wait for FCU connection
    while not rospy.is_shutdown() and not current_state.connected:
        rospy.loginfo("Waiting for FCU connection")
        rate.sleep()
    # say connected
    rospy.loginfo("Connected to FCU")

    # Create a pose object
    pose = PoseStamped()
    pose.pose.position.x = 0
    pose.pose.position.y = 0
    pose.pose.position.z = 1  # Set altitude to 1 meter

    # Send a few setpoints before starting
    for i in range(100, 0, -1):
        local_pos_pub.publish(pose)
        rate.sleep()
    
    last_request = rospy.Time.now()
    offb_set_mode = SetModeRequest()
    offb_set_mode.base_mode = 0
    offb_set_mode.custom_mode = "OFFBOARD"
    print("hello")
    arm_cmd = CommandBoolRequest()

    # Keep trying to set OFFBOARD mode
    while not rospy.is_shutdown():
        if current_state.mode != "OFFBOARD":
            rospy.loginfo("Setting mode to OFFBOARD")
            
            set_mode_client.call(offb_set_mode)
            # Wait a bit before trying again
            rospy.sleep(1)

        # Check if OFFBOARD mode is set, then arm the vehicle
        if current_state.mode == "OFFBOARD":
            rospy.loginfo("OFFBOARD mode set")
            if not current_state.armed:
                rospy.loginfo("Arming vehicle")
                arm_cmd.value = True
                arming_client.call(arm_cmd)
                rospy.sleep(1)  # Delay to avoid bombarding with requests

        local_pos_pub.publish(pose)
        rate.sleep()

if __name__ == '__main__':
    try:
        offb_node()
    except rospy.ROSInterruptException:
        pass
