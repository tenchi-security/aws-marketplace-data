import boto3
from csv import writer
from botocore.config import Config

all_regions = [x['RegionName'] for x in boto3.client('ec2').describe_regions()['Regions']]

with open("amis.csv", 'w', newline='') as csvfile:
    csvwriter = writer(csvfile)
    csvwriter.writerow(
        ['Region', 'ImageId', 'CreationDate', 'Name', 'PlatformDetails', 'ProductCode', 'State', 'SnapshotIds',
         'OwnerId'])
    for region in all_regions:
        client = boto3.client("ec2", config=Config(region_name=region))
        for image in client.describe_images(Owners=["aws-marketplace"], IncludeDeprecated=True)['Images']:
            for product_code in image.get('ProductCodes',[]):
                # combine valid snapshot IDs
                snapshot_ids = [x['Ebs']['SnapshotId'] for x in image['BlockDeviceMappings']
                                if 'Ebs' in x and 'SnapshotId' in x['Ebs']]
                snapshot_ids = [x for x in snapshot_ids if x is not None and x != ""]
                # write row
                csvwriter.writerow([region, image['ImageId'], image['CreationDate'], image['Name'],
                                    image['PlatformDetails'], product_code['ProductCodeId'], image['State'],
                                    ','.join(snapshot_ids), image['OwnerId']])
