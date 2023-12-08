import datetime

def datetimeFromBiliTime(bili_time:float):
    past=datetime.datetime(2023,9,5,8,0,0,0)
    past_bili_time=1693872000
    past_timestamp=past.timestamp()
    
    new_timestamp=bili_time-past_bili_time+past_timestamp
    
    return datetime.datetime.fromtimestamp(new_timestamp)

def format_time(seconds):
    # 计算小时，分钟和秒数
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    # 根据时长的不同，选择合适的输出格式
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"
    
def convert_to_seconds(time_str:str):
    # Split the time string by colon
    time_parts = time_str.split(":")
    # Check the number of parts
    if len(time_parts) == 3:
        # The format is hh:mm:ss
        hours, minutes, seconds = time_parts
        # Convert each part to integer and multiply by the corresponding factor
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    elif len(time_parts) == 2:
        # The format is mm:ss
        minutes, seconds = time_parts
        # Convert each part to integer and multiply by the corresponding factor
        return int(minutes) * 60 + int(seconds)
    else:
        # Invalid format
        return None