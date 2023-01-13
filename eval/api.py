import frappe

@frappe.whitelist(allow_guest=True)
def get_stock_qty(item_code, delivery_warehouse):
    if item_code and delivery_warehouse:
        try:
            actual_qty = frappe.db.get_value(
                "Bin", fieldname=["actual_qty"], filters={"warehouse": delivery_warehouse, "item_code": item_code}
            ) or 0
            return actual_qty
        except Exception as e:
            frappe.log_error(e, "get_stock_qty")
    else:
        return "{} not found".format(item_code)

def validate_stock(doc, method):
    for item in doc.items:
        available_qty = get_stock_qty(item.item_code, item.warehouse)
        if item.qty > available_qty:
            req_qty = item.qty - available_qty
            data = {
                'transaction_date': doc.transaction_date,
                'supplier': item.supplier,
                'item_code': item.item_code,
                'req_qty': req_qty,
                'rate': item.rate
            }
            create_po(data=data)

def create_po(data):
    doc = frappe.get_doc({
        'doctype': 'Purchase Order',
        'supplier': data.get('supplier'),
        'transaction_date': data.get('transaction_date')
    })
    doc.append("items", {
        "item_code": data.get('item_code'),
        "schedule_date": data.get('transaction_date'),
        'qty': data.get('req_qty'),
        'rate': data.get('rate')
    })
    doc.insert()
    doc.submit()
