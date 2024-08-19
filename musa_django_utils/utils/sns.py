from asyncio import gather
from logging import getLogger

import boto3
from asgiref.sync import async_to_sync, sync_to_async
from botocore import exceptions

logger = getLogger('sns-events')


class SnsWrapper:
    """Encapsulates Amazon SNS topic and subscription functions."""

    def __init__(self, topic_arn: str = None):
        """
        :param topic_arn: A SNS Topic arn.
        """
        self.client = boto3.client('sns')
        self.topic_arn = topic_arn

    @staticmethod
    def _parser_attributes(attributes):
        att_dict = {}
        if isinstance(attributes, dict):
            for key, value in attributes.items():
                if isinstance(value, dict) and 'Type' in value and 'Value' in value:
                    if value['Type'] == 'String':
                        att_dict[key] = {'DataType': 'String', 'StringValue': value['Value']}
                    elif value['Type'] == 'Binary':
                        att_dict[key] = {'DataType': 'Binary', 'BinaryValue': value['Value']}

                elif isinstance(value, str):
                    att_dict[key] = {'DataType': 'String', 'StringValue': value}
                elif isinstance(value, int):
                    att_dict[key] = {'DataType': 'String', 'StringValue': str(value)}
                elif isinstance(value, bytes):
                    att_dict[key] = {'DataType': 'Binary', 'BinaryValue': value}

        return att_dict

    def publish_message(self, message, attributes=None, **kwargs):
        """
        Publishes a message, with attributes, to a topic. Subscriptions can be filtered
        based on message attributes so that a subscription receives messages only
        when specified attributes are present.

        :param topic: The topic to publish to.
        :param message: The message to publish.
        :param attributes: The key-value attributes to attach to the message. Values
                           must be either `str` or `bytes`.
        :return: The ID of the message.
        """
        assert any([self.topic_arn, *[x in kwargs for x in ['topic', 'TopicArn', 'TargetArn', 'PhoneNumber']]])
        assert isinstance(attributes, dict) or attributes is None
        assert isinstance(message, (str, dict))

        kwargs['TopicArn'] = kwargs.pop('topic', self.topic_arn)
        kwargs['MessageAttributes'] = self._parser_attributes(kwargs.get('MessageAttributes', attributes))

        try:
            response = self.client.publish(Message=message, **kwargs)
            message_id = response['MessageId']
            logger.info('Published message in topic %s. with message_id %s', kwargs.get('TopicArn'), message_id)
        except exceptions.ClientError:
            logger.exception("Couldn't publish message to topic %s.", kwargs.get('TopicArn'))
            raise
        else:
            return message_id

    async def _apublish_batch_message(self, batch_message):
        _func = sync_to_async(self.publish_message)
        tasks = [_func(**m) for m in batch_message]
        return await gather(*tasks)

    def publish_batch_message(self, batch_message):
        return async_to_sync(self._apublish_batch_message)(batch_message)
