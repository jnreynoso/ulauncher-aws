import os
import string
import io
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction

class KeywordProcessor(object):
    def __init__(self, case_sensitive=False):
        self._keyword = '_keyword_'
        self._white_space_chars = set(['.', '\t', '\n', '\a', ' ', ','])
        try:
            # python 2.x
            self.non_word_boundaries = set(string.digits + string.letters + '_')
        except AttributeError:
            # python 3.x
            self.non_word_boundaries = set(string.digits + string.ascii_letters + '_')
        self.keyword_trie_dict = dict()
        self.case_sensitive = case_sensitive
        self._terms_in_trie = 0

    def __len__(self):
        return self._terms_in_trie

    def __contains__(self, word):
        if not self.case_sensitive:
            word = word.lower()
        current_dict = self.keyword_trie_dict
        len_covered = 0
        for char in word:
            if char in current_dict:
                current_dict = current_dict[char]
                len_covered += 1
            else:
                break
        return self._keyword in current_dict and len_covered == len(word)

    def __getitem__(self, word):
        if not self.case_sensitive:
            word = word.lower()
        current_dict = self.keyword_trie_dict
        len_covered = 0
        for char in word:
            if char in current_dict:
                current_dict = current_dict[char]
                len_covered += 1
            else:
                break
        if self._keyword in current_dict and len_covered == len(word):
            return current_dict[self._keyword]

    def __setitem__(self, keyword, clean_name=None):
        status = False
        if not clean_name and keyword:
            clean_name = keyword

        if keyword and clean_name:
            if not self.case_sensitive:
                keyword = keyword.lower()
            current_dict = self.keyword_trie_dict
            for letter in keyword:
                current_dict = current_dict.setdefault(letter, {})
            if self._keyword not in current_dict:
                status = True
                self._terms_in_trie += 1
            current_dict[self._keyword] = clean_name
        return status

    def __delitem__(self, keyword):
        status = False
        if keyword:
            if not self.case_sensitive:
                keyword = keyword.lower()
            current_dict = self.keyword_trie_dict
            character_trie_list = []
            for letter in keyword:
                if letter in current_dict:
                    character_trie_list.append((letter, current_dict))
                    current_dict = current_dict[letter]
                else:
                    # if character is not found, break out of the loop
                    current_dict = None
                    break
            # remove the characters from trie dict if there are no other keywords with them
            if current_dict and self._keyword in current_dict:
                # we found a complete match for input keyword.
                character_trie_list.append((self._keyword, current_dict))
                character_trie_list.reverse()

                for key_to_remove, dict_pointer in character_trie_list:
                    if len(dict_pointer.keys()) == 1:
                        dict_pointer.pop(key_to_remove)
                    else:
                        # more than one key means more than 1 path.
                        # Delete not required path and keep the other
                        dict_pointer.pop(key_to_remove)
                        break
                # successfully removed keyword
                status = True
                self._terms_in_trie -= 1
        return status

    def __iter__(self):
        raise NotImplementedError("Please use get_all_keywords() instead")

    def set_non_word_boundaries(self, non_word_boundaries):
        self.non_word_boundaries = non_word_boundaries

    def add_non_word_boundary(self, character):
        self.non_word_boundaries.add(character)

    def add_keyword(self, keyword, clean_name=None):
        return self.__setitem__(keyword, clean_name)

    def remove_keyword(self, keyword):
        return self.__delitem__(keyword)

    def get_keyword(self, word):
        return self.__getitem__(word)

    def add_keyword_from_file(self, keyword_file, encoding="utf-8"):
        if not os.path.isfile(keyword_file):
            raise IOError("Invalid file path {}".format(keyword_file))
        with io.open(keyword_file, encoding=encoding) as f:
            for line in f:
                if '=>' in line:
                    keyword, clean_name = line.split('=>')
                    self.add_keyword(keyword, clean_name.strip())
                else:
                    keyword = line.strip()
                    self.add_keyword(keyword)

    def add_keywords_from_dict(self, keyword_dict):
        for clean_name, keywords in keyword_dict.items():
            if not isinstance(keywords, list):
                raise AttributeError("Value of key {} should be a list".format(clean_name))

            for keyword in keywords:
                self.add_keyword(keyword, clean_name)

    def remove_keywords_from_dict(self, keyword_dict):
        for clean_name, keywords in keyword_dict.items():
            if not isinstance(keywords, list):
                raise AttributeError("Value of key {} should be a list".format(clean_name))

            for keyword in keywords:
                self.remove_keyword(keyword)

    def add_keywords_from_list(self, keyword_list):
        if not isinstance(keyword_list, list):
            raise AttributeError("keyword_list should be a list")

        for keyword in keyword_list:
            self.add_keyword(keyword)

    def remove_keywords_from_list(self, keyword_list):
        if not isinstance(keyword_list, list):
                raise AttributeError("keyword_list should be a list")

        for keyword in keyword_list:
            self.remove_keyword(keyword)

    def get_all_keywords(self, term_so_far='', current_dict=None):
        terms_present = {}
        if not term_so_far:
            term_so_far = ''
        if current_dict is None:
            current_dict = self.keyword_trie_dict
        for key in current_dict:
            if key == '_keyword_':
                terms_present[term_so_far] = current_dict[key]
            else:
                sub_values = self.get_all_keywords(term_so_far + key, current_dict[key])
                for key in sub_values:
                    terms_present[key] = sub_values[key]
        return terms_present

    def extract_keywords(self, sentence, span_info=False, max_cost=0):
        keywords_extracted = []
        if not sentence:
            # if sentence is empty or none just return empty list
            return keywords_extracted
        if not self.case_sensitive:
            sentence = sentence.lower()
        current_dict = self.keyword_trie_dict
        sequence_start_pos = 0
        sequence_end_pos = 0
        reset_current_dict = False
        idx = 0
        sentence_len = len(sentence)
        curr_cost = max_cost
        while idx < sentence_len:
            char = sentence[idx]
            # when we reach a character that might denote word end
            if char not in self.non_word_boundaries:

                # if end is present in current_dict
                if self._keyword in current_dict or char in current_dict:
                    # update longest sequence found
                    sequence_found = None
                    longest_sequence_found = None
                    is_longer_seq_found = False
                    if self._keyword in current_dict:
                        sequence_found = current_dict[self._keyword]
                        longest_sequence_found = current_dict[self._keyword]
                        sequence_end_pos = idx

                    # re look for longest_sequence from this position
                    if char in current_dict:
                        current_dict_continued = current_dict[char]

                        idy = idx + 1
                        while idy < sentence_len:
                            inner_char = sentence[idy]
                            if inner_char not in self.non_word_boundaries and self._keyword in current_dict_continued:
                                # update longest sequence found
                                longest_sequence_found = current_dict_continued[self._keyword]
                                sequence_end_pos = idy
                                is_longer_seq_found = True
                            if inner_char in current_dict_continued:
                                current_dict_continued = current_dict_continued[inner_char]
                            elif curr_cost > 0:
                                next_word = self.get_next_word(sentence[idy:])
                                current_dict_continued, cost, _ = next(
                                    self.levensthein(next_word, max_cost=curr_cost, start_node=current_dict_continued),
                                    ({}, 0, 0),
                                ) # current_dict_continued to empty dict by default, so next iteration goes to a `break`
                                curr_cost -= cost
                                idy += len(next_word) - 1
                                if not current_dict_continued:
                                    break
                            else:
                                break
                            idy += 1
                        else:
                            # end of sentence reached.
                            if self._keyword in current_dict_continued:
                                # update longest sequence found
                                longest_sequence_found = current_dict_continued[self._keyword]
                                sequence_end_pos = idy
                                is_longer_seq_found = True
                        if is_longer_seq_found:
                            idx = sequence_end_pos
                    current_dict = self.keyword_trie_dict
                    if longest_sequence_found:
                        keywords_extracted.append((longest_sequence_found, sequence_start_pos, idx))
                        curr_cost = max_cost
                    reset_current_dict = True
                else:
                    # we reset current_dict
                    current_dict = self.keyword_trie_dict
                    reset_current_dict = True
            elif char in current_dict:
                # we can continue from this char
                current_dict = current_dict[char]
            elif curr_cost > 0:
                next_word = self.get_next_word(sentence[idx:])
                current_dict, cost, _ = next(
                    self.levensthein(next_word, max_cost=curr_cost, start_node=current_dict),
                    (self.keyword_trie_dict, 0, 0)
                )
                curr_cost -= cost
                idx += len(next_word) - 1
            else:
                # we reset current_dict
                current_dict = self.keyword_trie_dict
                reset_current_dict = True
                # skip to end of word
                idy = idx + 1
                while idy < sentence_len:
                    char = sentence[idy]
                    if char not in self.non_word_boundaries:
                        break
                    idy += 1
                idx = idy
            # if we are end of sentence and have a sequence discovered
            if idx + 1 >= sentence_len:
                if self._keyword in current_dict:
                    sequence_found = current_dict[self._keyword]
                    keywords_extracted.append((sequence_found, sequence_start_pos, sentence_len))
            idx += 1
            if reset_current_dict:
                reset_current_dict = False
                sequence_start_pos = idx
        if span_info:
            return keywords_extracted
        return [value[0] for value in keywords_extracted]

    def replace_keywords(self, sentence, max_cost=0):
        if not sentence:
            # if sentence is empty or none just return the same.
            return sentence
        new_sentence = []
        orig_sentence = sentence
        if not self.case_sensitive:
            sentence = sentence.lower()
        current_word = ''
        current_dict = self.keyword_trie_dict
        current_white_space = ''
        sequence_end_pos = 0
        idx = 0
        sentence_len = len(sentence)
        curr_cost = max_cost
        while idx < sentence_len:
            char = sentence[idx]
            # when we reach whitespace
            if char not in self.non_word_boundaries:
                current_word += orig_sentence[idx]
                current_white_space = char
                # if end is present in current_dict
                if self._keyword in current_dict or char in current_dict:
                    # update longest sequence found
                    sequence_found = None
                    longest_sequence_found = None
                    is_longer_seq_found = False
                    if self._keyword in current_dict:
                        sequence_found = current_dict[self._keyword]
                        longest_sequence_found = current_dict[self._keyword]
                        sequence_end_pos = idx

                    # re look for longest_sequence from this position
                    if char in current_dict:
                        current_dict_continued = current_dict[char]
                        current_word_continued = current_word
                        idy = idx + 1
                        while idy < sentence_len:
                            inner_char = sentence[idy]
                            if inner_char not in self.non_word_boundaries and self._keyword in current_dict_continued:
                                current_word_continued += orig_sentence[idy]
                                # update longest sequence found
                                current_white_space = inner_char
                                longest_sequence_found = current_dict_continued[self._keyword]
                                sequence_end_pos = idy
                                is_longer_seq_found = True
                            if inner_char in current_dict_continued:
                                current_word_continued += orig_sentence[idy]
                                current_dict_continued = current_dict_continued[inner_char]
                            elif curr_cost > 0:
                                next_word = self.get_next_word(sentence[idy:])
                                current_dict_continued, cost, _ = next(
                                    self.levensthein(next_word, max_cost=curr_cost, start_node=current_dict_continued),
                                    ({}, 0, 0)
                                )
                                idy += len(next_word) - 1
                                curr_cost -= cost
                                current_word_continued += next_word  # just in case of a no match at the end
                                if not current_dict_continued:
                                    break
                            else:
                                break
                            idy += 1
                        else:
                            # end of sentence reached.
                            if self._keyword in current_dict_continued:
                                # update longest sequence found
                                current_white_space = ''
                                longest_sequence_found = current_dict_continued[self._keyword]
                                sequence_end_pos = idy
                                is_longer_seq_found = True
                        if is_longer_seq_found:
                            idx = sequence_end_pos
                            current_word = current_word_continued
                    current_dict = self.keyword_trie_dict
                    if longest_sequence_found:
                        curr_cost = max_cost
                        new_sentence.append(longest_sequence_found + current_white_space)
                        current_word = ''
                        current_white_space = ''
                    else:
                        new_sentence.append(current_word)
                        current_word = ''
                        current_white_space = ''
                else:
                    # we reset current_dict
                    current_dict = self.keyword_trie_dict
                    new_sentence.append(current_word)
                    current_word = ''
                    current_white_space = ''
            elif char in current_dict:
                # we can continue from this char
                current_word += orig_sentence[idx]
                current_dict = current_dict[char]
            elif curr_cost > 0:
                next_orig_word = self.get_next_word(orig_sentence[idx:])
                next_word = next_orig_word if self.case_sensitive else str.lower(next_orig_word)
                current_dict, cost, _ = next(
                    self.levensthein(next_word, max_cost=curr_cost, start_node=current_dict),
                    (self.keyword_trie_dict, 0, 0)
                )
                idx += len(next_word) - 1
                curr_cost -= cost
                current_word += next_orig_word  # just in case of a no match at the end
            else:
                current_word += orig_sentence[idx]
                # we reset current_dict
                current_dict = self.keyword_trie_dict
                # skip to end of word
                idy = idx + 1
                while idy < sentence_len:
                    char = sentence[idy]
                    current_word += orig_sentence[idy]
                    if char not in self.non_word_boundaries:
                        break
                    idy += 1
                idx = idy
                new_sentence.append(current_word)
                current_word = ''
                current_white_space = ''
            # if we are end of sentence and have a sequence discovered
            if idx + 1 >= sentence_len:
                if self._keyword in current_dict:
                    sequence_found = current_dict[self._keyword]
                    new_sentence.append(sequence_found)
                else:
                    new_sentence.append(current_word)
            idx += 1
        return "".join(new_sentence)

    def get_next_word(self, sentence):
        """
        Retrieve the next word in the sequence
        Iterate in the string until finding the first char not in non_word_boundaries
        Args:
            sentence (str): Line of text where we will look for the next word
        Returns:
            next_word (str): The next word in the sentence
        Examples:
            >>> from flashtext import KeywordProcessor
            >>> keyword_processor = KeywordProcessor()
            >>> keyword_processor.add_keyword('Big Apple')
            >>> 'Big'
        """
        next_word = str()
        for char in sentence:
            if char not in self.non_word_boundaries:
                break
            next_word += char
        return next_word

    def levensthein(self, word, max_cost=2, start_node=None):
        """
        Retrieve the nodes where there is a fuzzy match,
        via levenshtein distance, and with respect to max_cost
        Args:
            word (str): word to find a fuzzy match for
            max_cost (int): maximum levenshtein distance when performing the fuzzy match
            start_node (dict): Trie node from which the search is performed
        Yields:
            node, cost, depth (tuple): A tuple containing the final node,
                                      the cost (i.e the distance), and the depth in the trie
        Examples:
            >>> from flashtext import KeywordProcessor
            >>> keyword_processor = KeywordProcessor(case_sensitive=True)
            >>> keyword_processor.add_keyword('Marie', 'Mary')
            >>> next(keyword_processor.levensthein('Maria', max_cost=1))
            >>> ({'_keyword_': 'Mary'}, 1, 5)
            ...
            >>> keyword_processor = KeywordProcessor(case_sensitive=True
            >>> keyword_processor.add_keyword('Marie Blanc', 'Mary')
            >>> next(keyword_processor.levensthein('Mari', max_cost=1))
            >>> ({' ': {'B': {'l': {'a': {'n': {'c': {'_keyword_': 'Mary'}}}}}}}, 1, 5)
        """
        start_node = start_node or self.keyword_trie_dict
        rows = range(len(word) + 1)

        for char, node in start_node.items():
            yield from self._levenshtein_rec(char, node, word, rows, max_cost, depth=1)


    def _levenshtein_rec(self, char, node, word, rows, max_cost, depth=0):
        n_columns = len(word) + 1
        new_rows = [rows[0] + 1]
        cost = 0

        for col in range(1, n_columns):
            insert_cost = new_rows[col - 1] + 1
            delete_cost = rows[col] + 1
            replace_cost = rows[col - 1] + int(word[col - 1] != char)
            cost = min((insert_cost, delete_cost, replace_cost))
            new_rows.append(cost)

        stop_crit = isinstance(node, dict) and node.keys() & (self._white_space_chars | {self._keyword})
        if new_rows[-1] <= max_cost and stop_crit:
            yield node, cost, depth

        elif isinstance(node, dict) and min(new_rows) <= max_cost:
            for new_char, new_node in node.items():
                yield from self._levenshtein_rec(new_char, new_node, word, new_rows, max_cost, depth=depth + 1)

class GnomeSessionExtension(Extension):
    def __init__(self):
        super(GnomeSessionExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())

class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        items = []
        options = [
                        'ec2', 'ecs', 'rds', 's3', 'elasticbeanstalk', 'elasticache', 'cloudwatch', 'cloudformation', 'vpc', 'iam', 'ecr', 'eks', 'lambda', 'dynamodb',
                        'managementconsole', 'management', 'console',
                        'support', 'ticket', 'helpdesk', 'help',
                        'billing', 'budget', 'costs',
                        'pricingcalculator', 'pricing', 'price', 'prices', 'calculate', 'calculator',
                        'compare', 'instancecomparison', 'comparison',
                        'route53', 'dns', 'sqs', 'sns', 'ses', 'elasticsearch', 'kms', 'cloudfront', 'api', 'gateway',
                        'cloudtrail', 'secret'
                  ]
        my_list = event.query.split(" ")

        my_query = my_list[1]
        included = []

        keyword_processor = KeywordProcessor()

        keyword_dict = {
            "ec2": ['ec2', 'e', 'c', '2'],
            "Atlanta": ['ATL', 'Braves'],
            "Los Angeles": ['L.A', 'LA', 'Dogers']
        }

        keyword_processor.add_keywords_from_dict(keyword_dict)

        if my_query in options:
            if my_query in ['ec2']:
                items.append(get_ec2_item())
            elif my_query in ['ecs']:
                items.append(get_ecs_item())
            elif my_query in ['rds']:
                items.append(get_rds_item())
            elif my_query in ['s3']:
                items.append(get_s3_item())
            elif my_query in ['elasticbeanstalk']:
                items.append(get_elasticbeanstalk_item())
            elif my_query in ['elasticache']:
                items.append(get_elasticache_item())
            elif my_query in ['cloudwatch']:
                items.append(get_cloudwatch_item())
            elif my_query in ['cloudformation']:
                items.append(get_cloudformation_item())
            elif my_query in ['vpc']:
                items.append(get_vpc_item())
            elif my_query in ['iam']:
                items.append(get_iam_item())
            elif my_query in ['ecr']:
                items.append(get_ecr_item())
            elif my_query in ['eks']:
                items.append(get_eks_item())
            elif my_query in ['lambda']:
                items.append(get_lambda_item())
            elif my_query in ['dynamodb']:
                items.append(get_dynamodb_item())
            elif my_query in ['managementconsole', 'management', 'console'] and 'managementconsole' not in included:
                items.append(get_managementconsole_item())
                included.append('managementconsole')
            elif my_query in ['support', 'ticket', 'helpdesk', 'help'] and 'support' not in included:
                items.append(get_support_item())
                included.append('support')
            elif my_query in ['billing', 'budget', 'costs'] and 'billing' not in included:
                items.append(get_billing_item())
                included.append('billing')
            elif my_query in ['pricingcalculator', 'pricing', 'price', 'prices', 'calculate', 'calculator'] and 'pricingcalculator' not in included:
                items.append(get_pricingcalculator())
                included.append('pricingcalculator')
            elif my_query in ['compare', 'instancecomparison', 'comparison'] and 'compare' not in included:
                items.append(get_compare())
                included.append('compare')
            elif my_query in ['route53', 'dns'] and 'route53' not in included:
                items.append(get_route53_item())
                included.append('route53')
            elif my_query in ['sqs']:
                items.append(get_sqs_item())
            elif my_query in ['sns']:
                items.append(get_sns_item())
            elif my_query in ['ses']:
                items.append(get_ses_item())
            elif my_query in ['cloudfront']:
                items.append(get_cloudfront_item())
            elif my_query in ['kms']:
                items.append(get_kms_item())
            elif my_query in ['elasticsearch']:
                items.append(get_elasticsearch_item())
            elif my_query in ['api', 'gateway']:
                items.append(get_api_gateway_item())
            elif my_query in ['secret']:
                items.append(get_secret_item())
            elif my_query in ['cloudtrail']:
                items.append(get_cloudtrail_item())

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

