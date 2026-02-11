# add postgres triggers for the order status history audit trail
# these fire automatically on insert/update so we never miss a status change

from typing import Sequence, Union
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # trigger that logs every status change on existing orders
    op.execute("""
        CREATE OR REPLACE FUNCTION log_order_status_change()
        RETURNS TRIGGER AS $$
        BEGIN
            IF OLD.status IS DISTINCT FROM NEW.status THEN
                INSERT INTO order_status_history (order_id, old_status, new_status, changed_at)
                VALUES (NEW.id, OLD.status, NEW.status, NOW());
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS order_status_change_trigger ON orders;

        CREATE TRIGGER order_status_change_trigger
        AFTER UPDATE ON orders
        FOR EACH ROW
        EXECUTE FUNCTION log_order_status_change();
    """)

    # trigger that logs when a brand new order is created
    op.execute("""
        CREATE OR REPLACE FUNCTION log_order_creation()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO order_status_history (order_id, old_status, new_status, changed_at)
            VALUES (NEW.id, NULL, NEW.status, NOW());
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS order_creation_trigger ON orders;

        CREATE TRIGGER order_creation_trigger
        AFTER INSERT ON orders
        FOR EACH ROW
        EXECUTE FUNCTION log_order_creation();
    """)


def downgrade() -> None:
    # clean up triggers and functions
    op.execute("DROP TRIGGER IF EXISTS order_status_change_trigger ON orders;")
    op.execute("DROP FUNCTION IF EXISTS log_order_status_change();")
    op.execute("DROP TRIGGER IF EXISTS order_creation_trigger ON orders;")
    op.execute("DROP FUNCTION IF EXISTS log_order_creation();")
