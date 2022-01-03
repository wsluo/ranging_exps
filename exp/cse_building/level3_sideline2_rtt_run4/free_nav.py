#!/usr/bin/env python
import rospy
import tf
import numpy
import geometry_msgs.msg
from geometry_msgs.msg import Twist
from geometry_msgs.msg import PoseWithCovarianceStamped
from math import *
from nav_msgs.msg import Odometry
from std_msgs.msg import String
import tf2_ros
import copy
from numpy import genfromtxt
import sys
from datetime import datetime
import time

LINEAR_VELOCITY_MINIMUM_THRESHOLD  = 0.1
ANGULAR_VELOCITY_MINIMUM_THRESHOLD = 0.4

LINEAR_ACC = 0.2
LINEAR_DEC = 0.6

ANG_ACC = 0.4
ANG_DEC = 0.5

ANGULAR_SPEED=1
LINEAR_SPEED=0.65

class free_space_navigation():

    def poseCallback(self,pose_message):
        position = pose_message.pose.pose.position
        orientation = pose_message.pose.pose.orientation

        self.turtlebot_odom_pose.pose.pose.position.x=position.x
        self.turtlebot_odom_pose.pose.pose.position.y=position.y
        self.turtlebot_odom_pose.pose.pose.position.z=position.z

        self.turtlebot_odom_pose.pose.pose.orientation.w=orientation.w
        self.turtlebot_odom_pose.pose.pose.orientation.x=orientation.x
        self.turtlebot_odom_pose.pose.pose.orientation.y=orientation.y
        self.turtlebot_odom_pose.pose.pose.orientation.z=orientation.z


        logs.append([pose_message.header.stamp, position.x,position.y,position.z, orientation.x,orientation.y,orientation.z,orientation.w])
        #print pose_message.header.stamp, position.x,position.y,position.z, orientation.x,orientation.y,orientation.z,orientation.w
        #try:
        #    logfile.write(','.join([str(pose_message.header.stamp), str(position.x),str(position.y),str(position.z), str(orientation.x),str(orientation.y),str(orientation.z),str(orientation.w)]))
        #    logfile.write('\n')
        #except IOError:
        #    print("output file has been closed")
        

    def move_v1(self, speed, distance, isForward):
        #declare a Twist message to send velocity commands
        VelocityMessage = Twist()
        # declare tf transform listener: this transform listener will be used to listen and capture the transformation between
        # the odom frame (that represent the reference frame) and the base_footprint frame the represent moving frame
        listener = tf.TransformListener()

        #set the linear velocity to a positive value if isFoward is True
        if (isForward):
            VelocityMessage.linear.x =abs(speed)
        else: #else set the velocity to negative value to move backward
            VelocityMessage.linear.x =-abs(speed)

        # all velocities of other axes must be zero.
        VelocityMessage.linear.y =0
        VelocityMessage.linear.z =0
        #The angular velocity of all axes must be zero because we want  a straight motion
        VelocityMessage.angular.x = 0
        VelocityMessage.angular.y = 0
        VelocityMessage.angular.z =0

        distance_moved = 0.0
        loop_rate = rospy.Rate(10) # we publish the velocity at 10 Hz (10 times a second)


        #  First, we capture the initial transformation before starting the motion.
        # we call this transformation "init_transform"
        # It is important to "waitForTransform" otherwise, it might not be captured.

        try:
            #wait for the transform to be found

            listener.waitForTransform("/base_footprint", "/odom", rospy.Time(0),rospy.Duration(10.0))
            #Once the transform is found,get the initial_transform transformation.
            (trans,rot) = listener.lookupTransform('/base_footprint', '/odom', rospy.Time(0))
            #listener.lookupTransform("/base_footprint", "/odom", rospy.Time(0),init_transform)
            start = 0.5 * sqrt(trans[0] ** 2 + trans[1] ** 2)

        except Exception:
            rospy.Duration(1.0)

        distance_moved = 0

        while not rospy.is_shutdown():
            rospy.loginfo("Turtlebot moves forwards")

            self.velocityPublisher.publish(VelocityMessage)
            loop_rate.sleep()

            try:

                #wait for the transform to be found
                listener.waitForTransform("/base_footprint", "/odom", rospy.Time(0), rospy.Duration(10.0) )
                #Once the transform is found,get the initial_transform transformation.
                #listener.lookupTransform("/base_footprint", "/odom",rospy.Time(0))
                (trans,rot) = listener.lookupTransform('/base_footprint', '/odom', rospy.Time(0))
            except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
                rospy.Duration(1.0)

            # Method 1: Calculate the distance between the two transformations
            # Hint:
            #    --> transform.getOrigin().x(): represents the x coordinate of the transformation
            #    --> transform.getOrigin().y(): represents the y coordinate of the transformation
            #
            # calculate the distance moved
            end = 0.5 * sqrt(trans[0] ** 2 + trans[1] ** 2)
            distance_moved = distance_moved+abs(abs(float(end)) - abs(float(start)))
            if not (distance_moved<distance):
                break

            #finally, stop the robot when the distance is moved
        VelocityMessage.linear.x =0
        self.velocityPublisher.publish(VelocityMessage)




    # Method 3: we use coordinates of the robot to estimate the distance

    def move_v3(self, speed, distance, isForward):
        #declare a Twist message to send velocity commands
        VelocityMessage = Twist()
        # declare tf transform listener: this transform listener will be used to listen and capture the transformation between
        # the odom frame (that represent the reference frame) and the base_footprint frame the represent moving frame
        listener = tf.TransformListener()
        #declare tf transform
        initial_turtlebot_odom_pose = Odometry()
        #init_transform: is the transformation before starting the motion
        init_transform = geometry_msgs.msg.TransformStamped()
        #current_transformation: is the transformation while the robot is moving
        current_transform = geometry_msgs.msg.TransformStamped()

        #set the linear velocity to a positive value if isFoward is True
        #if (isForward):
        #    VelocityMessage.linear.x =abs(speed)
        #else: #else set the velocity to negative value to move backward
        #    VelocityMessage.linear.x =-abs(speed)
        VelocityMessage.linear.x =0
        # all velocities of other axes must be zero.
        VelocityMessage.linear.y =0
        VelocityMessage.linear.z =0
        #The angular velocity of all axes must be zero because we want  a straight motion
        VelocityMessage.angular.x = 0
        VelocityMessage.angular.y = 0
        VelocityMessage.angular.z = 0

        distance_moved = 0.0
        current_speed = 0.0
        loop_per_sec = 25
        loop_rate = rospy.Rate(loop_per_sec)
        #we update the initial_turtlebot_odom_pose using the turtlebot_odom_pose global variable updated in the callback function poseCallback
        #we will use deepcopy() to avoid pointers confusion
        initial_turtlebot_odom_pose = copy.deepcopy(self.turtlebot_odom_pose)

        initial_x=initial_turtlebot_odom_pose.pose.pose.position.x
        initial_y=initial_turtlebot_odom_pose.pose.pose.position.y


       # rospy.loginfo("Turtlebot moves forwards")
       # print initial_x,initial_y,"distance %s" %distance
        stopping = False
        while not rospy.is_shutdown():
            if current_speed <abs(speed) and not stopping:
                current_speed+=LINEAR_ACC/loop_per_sec
                if current_speed >= abs(speed):
                    current_speed=abs(speed)
            if isForward:
                VelocityMessage.linear.x=current_speed
            else:
                VelocityMessage.linear.x=-current_speed

            self.velocityPublisher.publish(VelocityMessage)

            loop_rate.sleep()

            current_x=self.turtlebot_odom_pose.pose.pose.position.x
            current_y=self.turtlebot_odom_pose.pose.pose.position.y


            distance_moved = sqrt((current_x - initial_x)**2 + (current_y - initial_y)**2)
           # print "x %s" %current_x,"y %s" %current_y,distance_moved, VelocityMessage.linear.x

            if abs(distance_moved-distance)<0.5*speed * speed/LINEAR_DEC:
                stopping = True
                current_speed-=LINEAR_DEC/loop_per_sec
                if current_speed<LINEAR_VELOCITY_MINIMUM_THRESHOLD:
                    current_speed = LINEAR_VELOCITY_MINIMUM_THRESHOLD

            if abs(distance_moved-distance)<0.02 or distance_moved>=distance:
                break

       # rospy.loginfo("Turtlebot finishes moving forwards")
        #finally, stop the robot when the distance is moved
        VelocityMessage.linear.x =0
        self.velocityPublisher.publish(VelocityMessage)

    def degree2radian(self, degreeAngle):
        return (degreeAngle/57.2957795)

    def rotate(self,angular_velocity,radians,clockwise):
        rotateMessage = Twist()
        angle_turned = 0.0
        angle_turned_acc = 0.0
       # angular_velocity = (-angular_velocity, ANGULAR_VELOCITY_MINIMUM_THRESHOLD)[angular_velocity > ANGULAR_VELOCITY_MINIMUM_THRESHOLD]

        while(radians > 2* pi):
            radians -= 2* pi

        rot = self.turtlebot_odom_pose.pose.pose.orientation

        #since the rotation is only in the Z-axes
        #start_angle = tf.transformations.#0.5 * sqrt(rot[2] ** 2)
        euler = tf.transformations.euler_from_quaternion([rot.x,rot.y,rot.z,rot.w])
        roll = euler[0]
        pitch = euler[1]
        start_angle = euler[2]

        rotateMessage.linear.x = rotateMessage.linear.y = 0.0
        rotateMessage.angular.z = ANGULAR_VELOCITY_MINIMUM_THRESHOLD #acc from 0

        #clockwise: negative angular speed, counter clockwise: positive angular speed
        if (clockwise):
            direction=-1
        else:
            direction=1
        rotateMessage.angular.z = rotateMessage.angular.z * direction

        loop_per_sec=25
        loop_rate = rospy.Rate(loop_per_sec)
        #rospy.loginfo("Turtlebot starts rotating")
        last_angle_turned=0
        last_wrapped_end_angle = start_angle

        STOPPING=False
        while not rospy.is_shutdown():

            if rotateMessage.angular.z <angular_velocity and not STOPPING:
               rotateMessage.angular.z+= direction*ANG_ACC/loop_per_sec

            self.velocityPublisher.publish(rotateMessage)

            loop_rate.sleep()

            current_rot = self.turtlebot_odom_pose.pose.pose.orientation

            #since the rotation is only in the Z-axes
            euler = tf.transformations.euler_from_quaternion([current_rot.x,current_rot.y,current_rot.z,current_rot.w])
            roll = euler[0]
            pitch = euler[1]
            end_angle = euler[2]


            angle_turned = min(abs(end_angle - start_angle),2*pi - abs(end_angle - start_angle))
            #angle_turned = abs(end_angle-start_angle)
            angle_turned_acc+= abs(angle_turned - last_angle_turned)

           # print start_angle,end_angle,angle_turned,"rot speed %s" %rotateMessage.angular.z

            if abs(angle_turned-radians)<0.5:
                STOPPING=True
                rotateMessage.angular.z-=direction * ANG_DEC/loop_per_sec
                if abs(rotateMessage.angular.z)<ANGULAR_VELOCITY_MINIMUM_THRESHOLD:
                    rotateMessage.angular.z = direction * ANGULAR_VELOCITY_MINIMUM_THRESHOLD


            if (angle_turned >= radians) or (angle_turned_acc >= radians):
                print "angle_turned: %s" %angle_turned
                break
            last_angle_turned=angle_turned
       # rospy.loginfo("Turtlebot ends rotating")
        rotateMessage.angular.z=0
        self.velocityPublisher.publish(rotateMessage)
        loop_rate.sleep()

    def calculateYaw( x1, y1, x2,y2):
        bearing = atan2((y2 - y1),(x2 - x1))
        #if(bearing < 0) bearing += 2 * PI
        bearing *= 180.0 / pi
        return bearing


    def moveSquare(self,sideLength):
        waypoints =[ [sideLength,0,0],[sideLength,sideLength,0],[0,sideLength,0],[0,0,0]] #counterclockwise
        self.follow_waypoints(waypoints)

    def follow_waypoints(self,waypoints):
        for waypoint in waypoints:
            self.goto(waypoint)


    def goto(self,point):
        forward=True
        current_x=self.turtlebot_odom_pose.pose.pose.position.x
        current_y=self.turtlebot_odom_pose.pose.pose.position.y
        current_z=self.turtlebot_odom_pose.pose.pose.position.z
        dist=sqrt( (current_x-point[0])**2 + (current_y-point[1])**2 + (current_z-point[2])**2 )

        current_rot = self.turtlebot_odom_pose.pose.pose.orientation

        euler = tf.transformations.euler_from_quaternion([current_rot.x,current_rot.y,current_rot.z,current_rot.w])
        current_angle = euler[2] #range: -pi to pi

        target_angle = atan2(point[1] - current_y, point[0] - current_x)
        # print "angles:",current_angle,target_angle
        if current_angle<0:
            current_angle+= 2*pi

        if target_angle<0:
            target_angle+= 2*pi

        to_rotate=abs(target_angle-current_angle)
        direction = target_angle < current_angle

        #to rotate faster
        if to_rotate > 2*pi - to_rotate:
            to_rotate = 2*pi - to_rotate
            direction = not direction
        if to_rotate > 0.8*pi:
            to_rotate = pi - to_rotate
            direction = not direction
            forward = not forward
        print to_rotate

        if direction:
            print "clockwise"
        else:
            print "counterclockwise"

        self.rotate(ANGULAR_SPEED, to_rotate,direction)
        self.move_v3(LINEAR_SPEED,dist,forward)
        rospy.sleep(0.1)

    def __init__(self):
        # initiliaze
        rospy.init_node('free_space_navigation', anonymous=True)

        # What to do you ctrl + c
        rospy.on_shutdown(self.shutdown)
        self.turtlebot_odom_pose = Odometry()
        pose_message = Odometry()
        self.velocityPublisher = rospy.Publisher('/cmd_vel_mux/input/teleop', Twist, queue_size=20)
        self.pose_subscriber = rospy.Subscriber("/robot_pose_ekf/odom_combined", PoseWithCovarianceStamped, self.poseCallback)

        rospy.sleep(1)
        
        if args.i=='sideline2':
            self.rotate(ANGULAR_SPEED,pi/2,False) #for preparation, comment out for typical routes
            self.move_v3(LINEAR_SPEED,0.5,True)
            self.rotate(ANGULAR_SPEED,pi/2,False)

        while not rospy.is_shutdown():
            #points=[[0,0,0]]
            #points=[[2,0,0],[4,0,0],[6,0,0],[4,0,0],[2,0,0],[0,0,0]]
            #if REVERSE:
            #    points=list(reversed(points[:-1]))+[[0,0,0]]
            #points = [ [1,0,0],[1,1,0],[0,1,0],[0,0,0]]
            self.follow_waypoints(waypoints)
            rospy.sleep(1.5)
            if time.time()-start_time > duration:
                for line in logs:
                    logfile.write(' '.join([str(x) for x in line])+'\n')

                logfile.write('### {}'.format(time.time())+'\n')
                logfile.close()
                self.goto([0,0,0])
                self.shutdown()
                print('Time Up!')
                break

    def shutdown(self):
        # stop turtlebot
        rospy.loginfo("Stop!!!")
        self.velocityPublisher.publish(Twist())
        rospy.sleep(2)


if __name__ == '__main__':
    try:
        import argparse
        parser = argparse.ArgumentParser(description="Flip a switch by setting a flag")
        parser.add_argument('-r', action='store_true')
        parser.add_argument('-i', type=str)
        parser.add_argument('-t',type=int)
        parser.add_argument('-d',type=int)

        args = parser.parse_args()
        REVERSE=False
        if args.r:
            REVERSE=True


        waypoints_file = args.i
        waypoints = genfromtxt(waypoints_file,delimiter='')


        logfile = open('./data/'+str(args.t)+'_'+args.i,'w')
        logfile.write('### LINEAR_VELOCITY_MINIMUM_THRESHOLD: {}'.format(LINEAR_VELOCITY_MINIMUM_THRESHOLD)+'\n')
        logfile.write('### ANGULAR_VELOCITY_MINIMUM_THRESHOLD: {}'.format(ANGULAR_VELOCITY_MINIMUM_THRESHOLD)+'\n')
        logfile.write('### LINEAR_ACC: {}'.format(LINEAR_ACC)+'\n')
        logfile.write('### LINEAR_DEC: {}'.format(LINEAR_DEC)+'\n')
        logfile.write('### ANG_ACC: {}'.format(ANG_ACC)+'\n')
        logfile.write('### ANG_DEC: {}'.format(ANG_DEC)+'\n')
        logfile.write('### ANGULAR_SPEED: {}'.format(ANGULAR_SPEED)+'\n')
        logfile.write('### LINEAR_SPEED: {}'.format(LINEAR_SPEED)+'\n')

        logs = []        

        scheduled_time = args.t
        while time.time()<scheduled_time:
            time.sleep(1/1000000)

        start_time=time.time()
        duration=args.d
        free_space_navigation()
        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo("node terminated.")
