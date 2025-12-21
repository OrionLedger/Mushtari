<<<<<<< HEAD
# from infrastructure import Mongo_DB_Module

# db = Mongo_DB_Module(
#     uri="mongodb://127.0.0.1:27017",
#     db_name="orion_ledger",
# )
# db.initialize_db()

# # Example operations
# db.add_record("test_collection", {"name": "Test Record", "value": 123})
# record = db.get_record("test_collection", {"name": "Test Record"})
# print(record)
# db.close_connection()

import comtradeapicall

SUBSCRIPTION_KEY = "ccc68c7328e44483bbaf07d6c6f1acd6"

mydf = comtradeapicall.previewFinalData(typeCode='C', freqCode='M', clCode='HS', period='202201',
                                        reporterCode='36', cmdCode='91', flowCode='M', partnerCode=None,
                                        partner2Code=None,
                                        customsCode=None, motCode=None, maxRecords=500, format_output='JSON',
                                        aggregateBy=None, breakdownMode='classic', countOnly=None, includeDesc=True)

print(mydf.columns)
print(mydf[["cmdCode", "cmdDesc", "primaryValue", "period", "refYear", "refMonth"]])
print(mydf[["cmdCode", "cmdDesc", "primaryValue", "period", "refYear", "refMonth"]].shape)
=======
>>>>>>> tamer
