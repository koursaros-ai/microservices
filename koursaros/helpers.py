import struct


def _parse_msg(body):
    """
    first three characters are the method, next
    sixteen are id, and last the rest is the message.

    :param body: bytes message
    :return method, msg_id, msg
    """
    return body[:3], body[4:19], body[19:]


def _int_to_16byte(integer):
    return struct.pack("xL", integer)
