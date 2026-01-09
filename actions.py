from typing import Any, Dict, List, Text
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import psycopg2
from psycopg2 import pool
import os

# Create a connection pool for PostgreSQL
db_pool = psycopg2.pool.SimpleConnectionPool(
    1, 20,
    host=os.getenv("DB_HOST", "localhost"),
    database=os.getenv("DB_NAME", "Products"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "Yabalshtroukplok1$"),
    port=os.getenv("DB_PORT", "5432")
)


class ActionLookupOrderStatus(Action):
    def name(self) -> Text:
        return "action_lookup_order_status"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        order_id = tracker.get_slot("order_id")
        
        if not order_id:
            dispatcher.utter_message(text="Please provide an order ID to check status.")
            return []
        
        conn = db_pool.getconn()
        try:
            cursor = conn.cursor()
            
            # Query your orders table
            cursor.execute("""
                SELECT 
                    order_id,
                    status,
                    order_date,
                    total_amount
                FROM orders
                WHERE order_id = %s
                LIMIT 1
            """, (order_id,))
            
            result = cursor.fetchone()
            
            if result:
                order_id_db, status, order_date, total_amount = result
                
                return [
                    SlotSet("order_id", order_id_db),
                    SlotSet("order_status", status),
                ]
            else:
                return [
                    SlotSet("order_id", order_id),
                    SlotSet("order_status", None),
                ]
        except Exception as e:
            print(f"Database error: {e}")
            dispatcher.utter_message(
                text="I'm having trouble accessing the order database right now. Please try again later."
            )
            return [SlotSet("order_status", None)]
        finally:
            cursor.close()
            db_pool.putconn(conn)


class ActionLookupProduct(Action):
    def name(self) -> Text:
        return "action_lookup_product"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        product_name = tracker.get_slot("product_name")
        
        if not product_name:
            dispatcher.utter_message(text="Please provide a product name to search.")
            return []
        
        conn = db_pool.getconn()
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    product_id,
                    product_name,
                    description,
                    unit_price,
                    stock,
                    is_active,
                    sku
                FROM products
                WHERE (LOWER(product_name) = LOWER(%s)
                   OR LOWER(product_name) LIKE LOWER(%s))
                AND is_active = TRUE
                ORDER BY
                    CASE WHEN LOWER(product_name) = LOWER(%s) THEN 1 ELSE 2 END   
                LIMIT 1
            """, (product_name, f"%{product_name}%", product_name))
            
            result = cursor.fetchone()
            
            if result:
                product_id, name, description, price, stock, is_active, sku = result
                available = stock > 0
                
                return [
                    SlotSet("product_id", product_id),
                    SlotSet("product_name", name),
                    SlotSet("product_description", description or "No description available."),
                    SlotSet("product_price", float(price)),
                    SlotSet("product_stock", stock),
                    SlotSet("product_available", available),
                ]
            else:
                return [
                    SlotSet("product_name", product_name),
                    SlotSet("product_available", None),
                    SlotSet("product_description", None),
                ]
        except Exception as e:
            print(f"Database error: {e}")
            dispatcher.utter_message(
                text="I'm having trouble accessing the product database right now. Please try again later."
            )
            return [SlotSet("product_available", None)]
        finally:
            cursor.close()
            db_pool.putconn(conn)


class ActionCreateSupportTicket(Action):
    def name(self) -> Text:
        return "action_create_support_ticket"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        issue_description = tracker.get_slot("issue_description")
        
        if not issue_description:
            dispatcher.utter_message(text="Please describe your issue.")
            return []
        
        conn = db_pool.getconn()
        try:
            cursor = conn.cursor()
            
            # Insert a new support ticket
            cursor.execute("""
                INSERT INTO support_tickets (description, status, created_at)
                VALUES (%s, 'open', NOW())
                RETURNING ticket_id
            """, (issue_description,))
            
            ticket_id = cursor.fetchone()[0]
            conn.commit()
            
            return [
                SlotSet("ticket_id", str(ticket_id)),
                SlotSet("issue_description", issue_description),
            ]
        except Exception as e:
            print(f"Database error: {e}")
            conn.rollback()
            dispatcher.utter_message(
                text="I'm having trouble creating your ticket right now. Please try again later."
            )
            return []
        finally:
            cursor.close()
            db_pool.putconn(conn)