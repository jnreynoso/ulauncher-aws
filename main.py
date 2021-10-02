from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction

def string_search_bf(*, text, pattern):
    n, m = len(text), len(pattern)
    for i in range(1 + (n - m)):
        match = True
        for j in range(m):
            if text[i + j] != pattern[j]:
                match = False
                break
        if match:
            return i

class GnomeSessionExtension(Extension):
    def __init__(self):
        super(GnomeSessionExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())

class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        items = []
        options = {
            'ec2': get_ec2_item, 'ecs': get_ecs_item, 'rds': get_rds_item, 's3': get_s3_item, 'elasticbeanstalk': get_elasticbeanstalk_item, 'elasticache': get_elasticache_item,
            'cloudwatch': get_cloudwatch_item, 'cloudformation': get_cloudformation_item, 'vpc': get_vpc_item, 'iam': get_iam_item, 'ecr': get_ecr_item, 'eks': get_eks_item,
            'lambda': get_lambda_item, 'dynamodb': get_dynamodb_item, 'managementconsole': get_managementconsole_item, 'management': get_managementconsole_item,
            'console': get_managementconsole_item, 'support': get_support_item, 'ticket': get_support_item, 'helpdesk': get_support_item, 'help': get_support_item, 'billing': get_billing_item,
            'budget': get_billing_item, 'costs': get_billing_item, 'pricingcalculator': get_pricingcalculator, 'pricing': get_pricingcalculator, 'price': get_pricingcalculator,
            'prices': get_pricingcalculator, 'calculate': get_pricingcalculator, 'calculator': get_pricingcalculator, 'compare': get_compare, 'instancecomparison': get_compare,
            'comparison': get_compare, 'route53': get_route53_item, 'dns': get_route53_item, 'sqs': get_sqs_item, 'sns': get_sns_item, 'ses': get_ses_item, 'elasticsearch': get_elasticsearch_item,
            'kms': get_kms_item, 'cloudfront': get_cloudfront_item, 'api': get_api_gateway_item, 'gateway': get_api_gateway_item, 'cloudtrail': get_cloudtrail_item, 'secret': get_secret_item
        }
        my_list = event.query.split(" ")

        my_query = my_list[1]
        included = []

        for option in options.keys():
            if string_search_bf(text=option, pattern="") != None:
                fnCall = options[option]
                items.append(fnCall())

        return RenderResultListAction(items)

def get_api_gateway_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS API Gateway',
                               description='AWS API Gateway',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/apigateway"))

def get_elasticsearch_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS Elasticsearch',
                               description='AWS Elasticsearch Service',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/es"))
def get_kms_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS KMS',
                               description='AWS Key Management Service',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/kms"))
def get_cloudfront_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS Cloudfront',
                               description='AWS CloudFront Manager',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/cloudfront"))
def get_ec2_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS EC2',
                               description='AWS Elastic Compute Cloud',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/ec2"))
def get_ecs_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS ECS',
                               description='EC2 Container Service',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/ecs"))

def get_rds_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS RDS',
                               description='AWS Relational Database Service',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/rds"))

def get_s3_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS S3',
                               description='AWS Simple Storage Service',
                               on_enter=OpenUrlAction("https://s3.console.aws.amazon.com/s3"))

def get_elasticbeanstalk_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS ElasticBeanstalk',
                               description='AWS ElasticBeanstalk Application Environment',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/elasticbeanstalk"))

def get_elasticache_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS ElastiCache',
                               description='AWS ElastiCache (Redis, Memcached, etc.)',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/elasticache"))

def get_cloudwatch_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS CloudWatch',
                               description='AWS CloudWatch Metrics and Monitoring',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/cloudwatch"))

def get_cloudformation_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS CloudFormation',
                               description='AWS Cloud Formation Cosole',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/cloudformation"))

def get_vpc_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS VPC',
                               description='AWS Virtual Private Cloud',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/vpc"))

def get_iam_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS IAM',
                               description='AWS Identity & Access Management',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/iam"))

def get_ecr_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS ECR',
                               description='AWS Elastic Container Registry',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/ecr"))

def get_eks_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS EKS',
                               description='AWS Kubernetes Management Service',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/eks"))

def get_lambda_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS Lambda',
                               description='AWS Lambda Serverless Computing',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/lambda"))

def get_dynamodb_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS DynamoDB',
                               description='AWS DynamoDB NoSQL Service',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/dynamodb"))

def get_managementconsole_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS Management Console',
                               description='Manage all your AWS infrastructure',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/console"))

def get_support_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS Support Console',
                               description='Access AWS customer and business support ticketing system',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/support"))

def get_billing_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS Billing Dashboard',
                               description='AWS Billing & Cost Management Center. Manage Billing, Budgets, Cost Explorer and Reports ',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/billing"))

def get_pricingcalculator():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS Pricing Calculator',
                               description='AWS Pricing Calculator',
                               on_enter=OpenUrlAction("https://calculator.s3.amazonaws.com/index.html"))

def get_compare():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS Instance Comparision',
                               description='EC2Instances.info Easy Amazon EC2 Instance Comparison',
                               on_enter=OpenUrlAction("https://www.ec2instances.info"))

def get_route53_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS Route 53',
                               description='AWS Route 53 Domain & DNS Service',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/route53"))

def get_sqs_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS Simple Queue Service',
                               description='AWS SQS Managed Message Queues',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/sqs"))

def get_sns_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS Simple Notification Service',
                               description='AWS SNS managed message topics for Pub/Sub',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/sns/v3"))

def get_ses_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS Simple Email Service',
                               description='AWS SES Email Sending and Receiving Service',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/ses"))

def get_secret_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS Secrets Manager',
                               description='AWS Secrets Manager',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/secretsmanager"))

def get_cloudtrail_item():
    return ExtensionResultItem(icon='images/icon.png',
                               name='AWS CloudTrail',
                               description='AWS CloudTrail',
                               on_enter=OpenUrlAction("https://console.aws.amazon.com/cloudtrail"))

if __name__ == '__main__':
    GnomeSessionExtension().run()

