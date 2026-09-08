"""Bounded, compatible QoS; watchdogs enforce control freshness separately."""
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, LivelinessPolicy
from rclpy.duration import Duration

SENSOR_QOS = QoSProfile(liveliness=LivelinessPolicy.AUTOMATIC, depth=5, reliability=ReliabilityPolicy.BEST_EFFORT)
LOGGING_QOS = QoSProfile(liveliness=LivelinessPolicy.AUTOMATIC, depth=100, reliability=ReliabilityPolicy.BEST_EFFORT)
CONTROL_QOS = QoSProfile(liveliness=LivelinessPolicy.AUTOMATIC, depth=1, reliability=ReliabilityPolicy.RELIABLE,
                         lifespan=Duration(seconds=0.5))
STATE_QOS = QoSProfile(liveliness=LivelinessPolicy.AUTOMATIC, depth=1, reliability=ReliabilityPolicy.RELIABLE,
                       durability=DurabilityPolicy.VOLATILE)
TRAJECTORY_QOS = QoSProfile(liveliness=LivelinessPolicy.AUTOMATIC, depth=1, reliability=ReliabilityPolicy.RELIABLE)
