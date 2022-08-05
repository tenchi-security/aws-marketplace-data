import logging
import sys
from csv import writer

import requests
from pyquery import PyQuery as pq

logger = logging.getLogger("aws-marketplace_scrapper")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


QUERY_URL = "https://aws.amazon.com/marketplace/api/awsmpdiscovery"
GET_CSRF_URL = "https://aws.amazon.com/marketplace/search?ref_=promo_banner"


def get_aws_marketplace_contentString(nextToken):
    if not nextToken:
        return "{\"MaxResults\":100,\"Sort\":{\"SortBy\":\"RELEVANT\",\"SortOrder\":\"DESCENDING\"},\"RequestContext\":{\"IntegrationId\":\"integ-wgprxonvth2vk\"}}"
    else:
        return "{\"MaxResults\":100,\"NextToken\":\"%s\",\"Sort\":{\"SortBy\":\"RELEVANT\",\"SortOrder\":\"DESCENDING\"},\"RequestContext\":{\"IntegrationId\":\"integ-wgprxonvth2vk\"}}" % nextToken


def get_aws_marketplace_data():
    page = pq(url=GET_CSRF_URL)
    meta_value = page("meta[id=AWSMP-CsrfToken]")
    logger.info("Got AWS Marketplace CSRF Token")

    session = requests.Session()
    session.get(GET_CSRF_URL, allow_redirects=True, headers={
        'authority': 'aws.amazon.com',
        'referer': 'https://aws.amazon.com/marketplace',
    })
    logger.info("Got AWS Marketplace Cookies")

    marketplace_request_with_cookies = session.post(QUERY_URL,
                                                    headers={
                                                        "awsmp-csrftoken": meta_value.attr("content")},
                                                    json={
                                                        "region": "us-east-1",
                                                        "headers": {
                                                            "Accept": "application/json",
                                                            "Accept-Encoding": "deflate, gzip",
                                                            "Content-Type": "application/x-amz-json-1.1",
                                                            "X-Amz-Target": "AWSMPDiscoveryService.SearchListings"
                                                        },
                                                        "contentString": get_aws_marketplace_contentString(None),
                                                        "method": "POST",
                                                        "operation": "SearchListings",
                                                        "path": "/"
                                                    })

    req_data = marketplace_request_with_cookies.json()
    products = []
    for prod in req_data['ListingSummaries']:
        products.append(create_product(prod))
    logger.info(f"Got first {len(products)} Marketplace products.")

    while 'NextToken' in req_data:
        marketplace_request_with_cookies = session.post(QUERY_URL,
                                                        headers={
                                                            "awsmp-csrftoken": meta_value.attr("content")},
                                                        json={
                                                            "region": "us-east-1",
                                                            "headers": {
                                                                "Accept": "application/json",
                                                                "Accept-Encoding": "deflate, gzip",
                                                                "Content-Type": "application/x-amz-json-1.1",
                                                                "X-Amz-Target": "AWSMPDiscoveryService.SearchListings"
                                                            },
                                                            "contentString": get_aws_marketplace_contentString(req_data['NextToken']),
                                                            "method": "POST",
                                                            "operation": "SearchListings",
                                                            "path": "/"
                                                        })
        req_data = marketplace_request_with_cookies.json()
        if marketplace_request_with_cookies.status_code != 200:
            break
        for prod in req_data['ListingSummaries']:
            products.append(create_product(prod))

        logger.info(f"Got {len(products)} Marketplace products so far.")

    logger.info(f"Got {len(products)} products from AWS Marketplace.")
    write_csv(products)


def create_product(prod):
    product_id = prod['ProductAttributes']['BaseProductId']
    title = prod['DisplayAttributes']['Title']
    seller_name = prod['ProductAttributes']['Creator']['DisplayName']
    seller_id = prod['ProductAttributes']['Creator']['Value']
    prod_id = prod['Id']
    marketplace_url = f"https://aws.amazon.com/marketplace/pp/{prod_id}"
    return {
        "title": title,
        "base_product_id": product_id,
        "seller_name": seller_name,
        "seller_id": seller_id,
        "marketplace_url": marketplace_url,
    }


def write_csv(products):

    with open("marketplace_products.csv", 'w', newline='') as csvfile:
        csvwriter = writer(csvfile)
        csvwriter.writerow(
            ['Title', 'BaseProductId', 'SellerName', 'SellerId', 'MarkerplaceUrl'])
        entries = 0
        for product in products:
            title = product['title']
            base_product_id = product['base_product_id']
            seller_name = product['seller_name']
            seller_id = product['seller_id']
            marketplace_url = product['marketplace_url']
            logger.info(f"Processing {title}...")

            # write row
            csvwriter.writerow(
                [title, base_product_id, seller_name, seller_id, marketplace_url])
            entries += 1
        logger.info(f"Ended. Wrote {entries}.")


get_aws_marketplace_data()
