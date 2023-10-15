# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

import sqlite3, re


class InitUsername(Action):
    def name(self):
        return "action_init_username"

    def run(self, dispatcher, tracker: Tracker, domain):
        user_name = tracker.get_slot("user_name")
        if not user_name:
            dispatcher.utter_message("What is your name?")
        else:
            # 打招呼
            dispatcher.utter_message("Welcome %s.How can I help you?" % user_name)
        return [SlotSet("user_name", user_name)]


class ActionSelectSeat(Action):
    def name(self):
        return "action_select_seat"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        conn = sqlite3.connect("rasa_db.db")
        cursor = conn.cursor()
        user_name = tracker.get_slot("user_name")
        select_seat = tracker.get_slot("seat")
        film_name = tracker.get_slot("film_name")
        print("user_name is {}".format(user_name))
        print("film_name is {}".format(film_name))
        print("select_seat is {}".format(select_seat))

        if select_seat is None:
            dispatcher.utter_message("Please select a seat.")
            return []
        result = re.match(r"Row (\d+), Seat (\d+)", select_seat)
        row = None
        col = None
        if result:
            row = result.group(1)
            col = result.group(2)
        # select_seat = str(select_seat).replace("/select_", "").split("_")
        # row = select_seat[0]
        # col = select_seat[1]
        seat = f"({row},{col})"
        if user_name is None:
            dispatcher.utter_message("Please provide your name.")
            return []
        if seat is None:
            dispatcher.utter_message("Please select a seat.")
            return []
        if film_name is None:
            dispatcher.utter_message("Please select a film.")
            return []
        try:
            # 查询用户是否在数据库
            cursor.execute(
                "select user_name, film_name, seat from flight where user_name = ?",
                (user_name,),
            )
            result = cursor.fetchone()
            if result and result[1] is not None and result[2] is None:
                # 更新 seat
                cursor.execute(
                    "update flight set seat = ? where user_name = ?",
                    (seat, user_name),
                )
                conn.commit()
                # 提示用户票已经订了
                dispatcher.utter_message("Your ticket has been booked successfully!")
            else:
                dispatcher.utter_message("Please select a movie.")

        except Exception as e:
            # 提示用户 一个人只能订一张票
            dispatcher.utter_message("You can only book one ticket at a time.")
            print(e)
        finally:
            conn.close()

        return [SlotSet("seat", None), SlotSet("film_name", None)]


class QueryTicket(Action):
    def name(self):
        return "action_query_ticket"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ):
        conn = sqlite3.connect("rasa_db.db")
        cursor = conn.cursor()
        user_name = tracker.get_slot("user_name")
        if not user_name:
            dispatcher.utter_message("Please provide your name.")
            return [SlotSet("film_name", None), SlotSet("seat", None)]
        cursor.execute(
            "select user_name, seat, film_name from flight where user_name = ?",
            (user_name,),
        )
        result = cursor.fetchone()
        if result:
            # 告诉用户购买的电影票是什么
            # seat 的格式 是(1,3)
            row = result[1].replace("(", "").replace(")", "").split(",")[0]
            col = result[1].replace("(", "").replace(")", "").split(",")[1]
            dispatcher.utter_message(
                "%s.Your ticket is booked for %s at Row %s, Seat %s."
                % (result[0], result[2], row, col)
            )
        else:
            dispatcher.utter_message("Sorry, your ticket is not booked.")

        conn.close()

        return [SlotSet("film_name", None), SlotSet("seat", None)]


# 取消机票
class ActionCancelTicket(Action):
    def name(self):
        return "action_cancel_ticket"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ):
        conn = sqlite3.connect("rasa_db.db")
        cursor = conn.cursor()
        user_name = tracker.get_slot("user_name")
        if not user_name:
            dispatcher.utter_message("Please provide your name.")
            return [SlotSet("film_name", None), SlotSet("seat", None)]
        # 先查询用户是否已经预订
        cursor.execute(
            "select user_name from flight where user_name = ?",
            (user_name,),
        )
        result = cursor.fetchone()
        if not result:
            dispatcher.utter_message("Sorry, your ticket is not booked.")
            return [SlotSet("film_name", None), SlotSet("seat", None)]
        try:
            cursor.execute(
                "delete from flight where user_name = ?",
                (user_name,),
            )
            conn.commit()
            dispatcher.utter_message("Your ticket has been canceled.")
        except Exception as e:
            dispatcher.utter_message("Sorry, your ticket is not booked.")
            print(e)
        finally:
            conn.close()
        return [SlotSet("film_name", None), SlotSet("seat", None)]


class ActionSelectFilm(Action):
    def name(self):
        return "action_select_film"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        conn = sqlite3.connect("rasa_db.db")
        cursor = conn.cursor()
        user_name = tracker.get_slot("user_name")
        selected_option = tracker.get_slot("film_name")
        print("user_name is {}".format(user_name))
        print("film_name is {}".format(selected_option))

        film_name = None
        if (
            "movie_1" in selected_option
            or "The Shawshank Redemption" in selected_option
        ):
            # 处理选项 1 的逻辑
            film_name = "The Shawshank Redemption"
        elif "movie_2" in selected_option or "The Dark Knight" in selected_option:
            # 处理选项 2 的逻辑
            film_name = "The Dark Knight"
        elif "movie_3" in selected_option or "Godfather" in selected_option:
            # 处理选项 3 的逻辑
            film_name = "Godfather"
        else:
            # print(selected_option)
            dispatcher.utter_message("Invalid film selected.")
        if user_name is None:
            dispatcher.utter_message("Please provide your name.")
            return []
        if film_name is None:
            dispatcher.utter_message("Please provide film name.")
            return []
        try:
            # 首先查询有无该用户
            cursor.execute(
                "select user_name, film_name, seat from flight where user_name = ?",
                (user_name,),
            )
            result = cursor.fetchone()
            if result and None not in result:
                dispatcher.utter_message("You have already booked a ticket.")
                return []
            # 再插入数据
            cursor.execute(
                "insert into flight (user_name, film_name) values (?, ?)",
                (user_name, film_name),
            )
            conn.commit()
        except Exception as e:
            print(e)
        finally:
            conn.close()
        dispatcher.utter_button_message(
            # 选择座位
            "Which seat do you want?",
            buttons=[
                {"title": "Row 1, Seat 1", "payload": "/select_1_1"},
                {"title": "Row 1, Seat 2", "payload": "/select_1_2"},
                {"title": "Row 1, Seat 3", "payload": "/select_1_3"},
            ],
        )
        return [SlotSet("film_name", film_name), SlotSet("user_name", user_name)]
