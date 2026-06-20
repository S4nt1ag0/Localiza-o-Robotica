#!/usr/bin/env python
import math

import rospy
from nav_msgs.msg import Odometry
from sensor_msgs.msg import NavSatFix, NavSatStatus


EARTH_RADIUS_M = 6378137.0


class GpsToOdom(object):
    def __init__(self):
        self.frame_id = rospy.get_param("~frame_id", "odom")
        self.child_frame_id = rospy.get_param("~child_frame_id", "gps_link")
        self.use_first_fix_as_origin = rospy.get_param("~use_first_fix_as_origin", True)
        self.origin_lat = rospy.get_param("~origin_latitude", None)
        self.origin_lon = rospy.get_param("~origin_longitude", None)
        self.origin_alt = rospy.get_param("~origin_altitude", 0.0)
        self.position_covariance = rospy.get_param("~position_covariance", 4.0)

        if not self.use_first_fix_as_origin and (self.origin_lat is None or self.origin_lon is None):
            raise rospy.ROSInitException("Set origin_latitude/origin_longitude or enable use_first_fix_as_origin")

        self.pub = rospy.Publisher("/gps/odom", Odometry, queue_size=10)
        self.sub = rospy.Subscriber("/fix", NavSatFix, self.fix_cb, queue_size=10)

    def fix_cb(self, msg):
        if msg.status.status == NavSatStatus.STATUS_NO_FIX:
            rospy.logwarn_throttle(5.0, "Ignoring GPS sample without fix")
            return

        if self.origin_lat is None or self.origin_lon is None:
            self.origin_lat = msg.latitude
            self.origin_lon = msg.longitude
            self.origin_alt = msg.altitude
            rospy.loginfo("GPS local origin set to lat=%.8f lon=%.8f", self.origin_lat, self.origin_lon)

        lat = math.radians(msg.latitude)
        lon = math.radians(msg.longitude)
        lat0 = math.radians(self.origin_lat)
        lon0 = math.radians(self.origin_lon)

        x = (lon - lon0) * math.cos(lat0) * EARTH_RADIUS_M
        y = (lat - lat0) * EARTH_RADIUS_M
        z = msg.altitude - self.origin_alt

        odom = Odometry()
        odom.header.stamp = msg.header.stamp if msg.header.stamp else rospy.Time.now()
        odom.header.frame_id = self.frame_id
        odom.child_frame_id = self.child_frame_id
        odom.pose.pose.position.x = x
        odom.pose.pose.position.y = y
        odom.pose.pose.position.z = z
        odom.pose.pose.orientation.w = 1.0

        cov = list(msg.position_covariance)
        if not any(cov):
            cov = [self.position_covariance, 0.0, 0.0,
                   0.0, self.position_covariance, 0.0,
                   0.0, 0.0, self.position_covariance]

        odom.pose.covariance[0] = cov[0]
        odom.pose.covariance[1] = cov[1]
        odom.pose.covariance[6] = cov[3]
        odom.pose.covariance[7] = cov[4]
        odom.pose.covariance[14] = cov[8]
        odom.pose.covariance[35] = 9999.0
        self.pub.publish(odom)


if __name__ == "__main__":
    rospy.init_node("gps_to_odom")
    GpsToOdom()
    rospy.spin()
