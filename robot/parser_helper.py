import argparse

def sc_subscribe(args):
    parser=argparse.ArgumentParser()
    # parser.add_argument('channel_id',type=int)
    parser.add_argument('room_id',type=int)
    return parser.parse_args(args)