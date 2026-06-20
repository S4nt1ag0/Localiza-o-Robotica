#!/usr/bin/env python
import rospy
from gazebo_msgs.srv import GetModelState
from nav_msgs.msg import Odometry


class GroundTruthOdomPublisher(object):
    def __init__(self):
        self.model_name = rospy.get_param("~model_name", "husky")
        self.frame_id = rospy.get_param("~frame_id", "odom")
        self.child_frame_id = rospy.get_param("~child_frame_id", "base_link_gt")
        self.rate_hz = rospy.get_param("~rate", 30.0)
        self.pub = rospy.Publisher("/gt/odom", Odometry, queue_size=10)
        rospy.wait_for_service("/gazebo/get_model_state")
        self.get_state = rospy.ServiceProxy("/gazebo/get_model_state", GetModelState)

    def run(self):
        rate = rospy.Rate(self.rate_hz)
        while not rospy.is_shutdown():
            try:
                state = self.get_state(model_name=self.model_name)
            except rospy.ServiceException as exc:
                rospy.logwarn_throttle(5.0, "Could not read Gazebo ground truth: %s", exc)
                rate.sleep()
                continue

            if not state.success:
                rospy.logwarn_throttle(5.0, "Gazebo model '%s' not found", self.model_name)
                rate.sleep()
                continue

            msg = Odometry()
            msg.header.stamp = rospy.Time.now()
            msg.header.frame_id = self.frame_id
            msg.child_frame_id = self.child_frame_id
            msg.pose.pose = state.pose
            msg.twist.twist = state.twist
            self.pub.publish(msg)
            rate.sleep()


if __name__ == "__main__":
    rospy.init_node("gt_odom_publisher")
    GroundTruthOdomPublisher().run()
