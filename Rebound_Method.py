#!/usr/bin/ehttps://cs231n.github.io/ nv python
import numpy as np
import rospy
import argparse 
from geometry_msgs.msg import PoseStamped
from geometry_msgs.msg import TwistStamped
from sensor_msgs.msg import LaserScan
#parameters 
speed=10
oa_radius=10

pub1 = rospy.Publisher('/mavros/setpoint_position/local', PoseStamped, queue_size=10)

pub_vel=rospy.Publisher('/mavros/setpoint_velocity/cmd_vel',TwistStamped,queue_size=20)


def callback_lidar(msg): #takes lidar values and sees if an object is detected
    counter =0
    start_ind=int((-np.pi/2-msg.angle_min)/msg.angle_increment)
    stop_ind=int((msg.angle_max-np.pi/2)/msg.angle_increment)

    for i in range(0,720):
        if msg.ranges[i]<oa_radius and msg.ranges[i]>1:
            print(msg.ranges[i])
            rospy.loginfo("object detected")
            counter=1
            #stop_now() #stops drone 
            break
    
    if counter == 1:
        rebound(msg) # rebound is called 

def setpoint(args):
    point = PoseStamped()
    point.pose.position.x = args.x
    point.pose.position.y = args.y
    point.pose.position.z = args.z
    for i in range(100):
        pub1.publish(point)
    rospy.sleep(1.)
    rospy.loginfo('Setpoint added')


def oa_detect():   # connects to subscriber 
    rospy.Subscriber('/spur/laser/scan',LaserScan,callback_lidar)
    print('inside OA detect')

                
def rebound(msg): # finds the rebound angle by the algo
    rospy.loginfo('Rebound called')
    alpha_o=msg.angle_increment
    
    sum_di=0
    sum_idi=0
    j = -np.pi/msg.angle_increment  #initalise index 
    for i in range(0,720):
        if msg.ranges[i]>msg.range_min and msg.ranges[i]<msg.range_max:
               sum_di=sum_di + msg.ranges[i]
               sum_idi=sum_idi + j*msg.ranges[i]
        j=j+1

    ang=alpha_o*sum_idi/sum_di
    rebound_pub(ang)

def rebound_pub(ang): #publishes the calculated angle
    rospy.loginfo('publishing rebound angle')
    vel=TwistStamped()
    ang=ang+np.pi/2
    vel.twist.linear.x=speed*np.cos(ang)
    vel.twist.linear.y=speed*np.sin(ang)
    vel.twist.linear.z=0
    for i in range(100):
        pub_vel.publish(vel)
    rospy.sleep(1.)
    oa_detect()
    
def stop_now():  #stops the drone 
    vel=TwistStamped()
    vel.twist.linear.x=0
    vel.twist.linear.y=0
    vel.twist.linear.z=0
    rospy.loginfo('Stopping drone')
    for i in range(100):
        pub_vel.publish(vel)



if __name__=="__main__":
    parser = argparse.ArgumentParser(description="setpoint/postition")
    parser.add_argument('-x', '--x', type=int, help="x component of point")
    parser.add_argument('-y', '--y', type=int, help="y component of point")
    parser.add_argument('-z', '--z', type=int, help="z component of point")
    args = parser.parse_args()
    print(args.x)
    print(args.y)
    print(args.z)
    rospy.init_node("OA",anonymous=True)
    r = rospy.Rate(10)
    try:
        while not rospy.is_shutdown():
            rospy.loginfo('reran loop')
            setpoint(args)
            oa_detect()
            r.sleep()

    except rospy.ROSInterruptException:
        pass
