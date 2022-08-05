import boto3
import logging
import sys
from csv import writer
from botocore.config import Config

logger = logging.getLogger("aws-marketplace_data")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

all_regions = sorted([x['RegionName'] for x in boto3.client('ec2').describe_regions()['Regions']])

with open("amis.csv", 'w', newline='') as csvfile:
    csvwriter = writer(csvfile)
    csvwriter.writerow(
        ['Region', 'ImageId', 'CreationDate', 'Name', 'Description', 'PlatformDetails', 'ProductCode', 'ProductId',
         'State', 'SnapshotIds', 'OwnerId'])
    entries = 0
    for region in all_regions:
        logger.info(f"Processing {region}...")
        client = boto3.client("ec2", config=Config(region_name=region))
        for image in client.describe_images(Owners=["aws-marketplace"], IncludeDeprecated=True)['Images']:
            for product_code in image.get('ProductCodes', []):
                if product_code['ProductCodeType'] != "marketplace":
                    continue

                # combine valid snapshot IDs
                snapshot_ids = [x['Ebs']['SnapshotId'] for x in image['BlockDeviceMappings']
                                if 'Ebs' in x and 'SnapshotId' in x['Ebs']]
                snapshot_ids = [x for x in snapshot_ids if x is not None and x != ""]
                # write row
                csvwriter.writerow([region, image['ImageId'], image['CreationDate'], image['Name'],
                                    image.get('Description', ''), image['PlatformDetails'],
                                    product_code['ProductCodeId'], image['State'], ','.join(snapshot_ids),
                                    image['OwnerId']])
                entries += 1
        logger.info(f"Ended {region}, {entries} written so far.")

logger.info("Processing ended successfully.")
