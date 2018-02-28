#!/usr/bin/env python
import rospy
from car_model.srv import OptControl
from geometry_msgs.msg import Point

print('POPOPOPOPOPO')

rospy.init_node('acado_client')
rospy.wait_for_service('solve_rocket')
rospy.loginfo('End of wait for rocket')
print()
print()
print('BBBBBBBBBBBBBBBBBBBBBBBBBB')

try:
    opt_control = rospy.ServiceProxy('solve_rocket', OptControl)
    p1 = Point(1., 4., 0)
    p2 = Point(6., 8., 0)
    resp = opt_control(p1, p2)
    print()
    print()
    print('RESPONSSSSE')
    print(resp.success)
    print(resp)
except rospy.ServiceException, e:
    print "Service call failed: %s" % e
