from .models import CourierType, IntervalTime

import datetime


class DateTimeHelper:

    @staticmethod
    def get_interval_by_string(s: str):
        if len(s) != 11 or s.find('-') != 5 or len(s.split('-')) != 2:
            return False
        helper = s.split('-')
        try:
            left = datetime.datetime.strptime(helper[0], "%H:%M").time()
            right = datetime.datetime.strptime(helper[1], "%H:%M").time()
            return left, right
        except ValueError:
            return False

    @staticmethod
    def get_interval_time_list(arr) -> [IntervalTime]:
        intervals: [IntervalTime] = []
        for i in arr:
            interval = DateTimeHelper.get_interval_by_string(i)
            if interval:
                intervals.append(IntervalTime(start_time=interval[0], finish_time=interval[1]))
        return intervals

    @staticmethod
    def get_list_str_working_hours(intervals: [IntervalTime]) -> [str]:
        list_intervals = []
        for interval in intervals:
            list_intervals.append(str(interval))
        return list_intervals

    # получить список интервалов для фильтра. если х = 1, то start < finish, -1 -- start > finish
    @staticmethod
    def get_list_interval_for_filter(arr: [IntervalTime], x: int):
        intervals = []
        for interval in arr:
            if x == 1 and interval.start_time < interval.finish_time:
                intervals.append(interval)
            if x == -1 and interval.start_time > interval.finish_time:
                intervals.append(interval)
        return intervals

    @staticmethod
    def get_datetime_by_iso_str(date: str) -> datetime.datetime:
        try:
            a = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")
            return a
        except ValueError:
            return datetime.datetime.strptime(datetime.datetime.now(), "%Y-%m-%dT%H:%M:%S.%fZ")
