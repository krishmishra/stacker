from troposphere import Output, Sub, Join, Ref
from troposphere import iam

from awacs.aws import Policy, Statement
import awacs
import awacs.s3
import awacs.cloudformation
import awacs.iam

from troposphere.cloudformation import WaitConditionHandle

from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import (
    CFNCommaDelimitedList,
    CFNNumber,
    CFNString,
    EC2KeyPairKeyName,
    EC2SecurityGroupId,
    EC2SubnetIdList,
    EC2VPCId,
)


class FunctionalTests(Blueprint):
    """This creates a stack with an IAM user and access key for running the
    functional tests for stacker.
    """

    VARIABLES = {
        "StackerNamespace": {
            "type": CFNString,
            "description": "The stacker namespace that the tests will use. "
                           "Access to cloudformation will be restricted to "
                           "only allow access to stacks with this prefix."},
        "StackerBucket": {
            "type": CFNString,
            "description": "The name of the bucket that the tests will use "
                           "for uploading templates."}
    }

    def create_template(self):
        t = self.template

        bucket_arn = Sub("arn:aws:s3:::${StackerBucket}*")
        cloudformation_scope = Sub(
            "arn:aws:cloudformation:${AWS::Region}:${AWS::AccountId}:"
            "stack/${StackerNamespace}-*")
        changeset_scope = "*"

        # This represents the precise IAM permissions that stacker itself
        # needs.
        stacker_policy = iam.Policy(
            PolicyName="Stacker",
            PolicyDocument=Policy(
                Statement=[
                    Statement(
                        Effect="Allow",
                        Resource=[bucket_arn],
                        Action=[
                            awacs.s3.ListBucket,
                            awacs.s3.GetBucketLocation,
                            awacs.s3.CreateBucket]),
                    Statement(
                        Effect="Allow",
                        Resource=[bucket_arn],
                        Action=[
                            awacs.s3.GetObject,
                            awacs.s3.GetObjectAcl,
                            awacs.s3.PutObject,
                            awacs.s3.PutObjectAcl]),
                    Statement(
                        Effect="Allow",
                        Resource=[changeset_scope],
                        Action=[
                            awacs.cloudformation.DescribeChangeSet]),
                    Statement(
                        Effect="Deny",
                        Resource=[Ref("AWS::StackId")],
                        Action=[
                            awacs.cloudformation.Action("*")]),
                    Statement(
                        Effect="Allow",
                        Resource=[cloudformation_scope],
                        Action=[
                            awacs.cloudformation.GetTemplate,
                            awacs.cloudformation.CreateChangeSet,
                            awacs.cloudformation.DeleteStack,
                            awacs.cloudformation.CreateStack,
                            awacs.cloudformation.UpdateStack,
                            awacs.cloudformation.DescribeStacks])]))

        user = t.add_resource(
            iam.User(
                "FunctionalTestUser",
                Policies=[
                    stacker_policy]))

        t.add_output(Output("User", Value=Ref(user)))


class Dummy(Blueprint):
    VARIABLES = {
        "StringVariable": {
            "type": str,
            "default": ""}
    }

    def create_template(self):
        self.template.add_resource(WaitConditionHandle("Dummy"))
        self.template.add_output(Output("DummyId", Value="dummy-1234"))


class VPC(Blueprint):
    VARIABLES = {
        "AZCount": {
            "type": int,
            "default": 2,
        },
        "PrivateSubnets": {
            "type": CFNCommaDelimitedList,
            "description": "Comma separated list of subnets to use for "
                           "non-public hosts. NOTE: Must have as many subnets "
                           "as AZCount"},
        "PublicSubnets": {
            "type": CFNCommaDelimitedList,
            "description": "Comma separated list of subnets to use for "
                           "public hosts. NOTE: Must have as many subnets "
                           "as AZCount"},
        "InstanceType": {
            "type": CFNString,
            "description": "NAT EC2 instance type.",
            "default": "m3.medium"},
        "BaseDomain": {
            "type": CFNString,
            "default": "",
            "description": "Base domain for the stack."},
        "InternalDomain": {
            "type": CFNString,
            "default": "",
            "description": "Internal domain name, if you have one."},
        "CidrBlock": {
            "type": CFNString,
            "description": "Base CIDR block for subnets.",
            "default": "10.128.0.0/16"},
        "ImageName": {
            "type": CFNString,
            "description": "The image name to use from the AMIMap (usually "
                           "found in the config file.)",
            "default": "NAT"},
        "UseNatGateway": {
            "type": CFNString,
            "allowed_values": ["true", "false"],
            "description": "If set to true, will configure a NAT Gateway"
                           "instead of NAT instances.",
            "default": "false"},
    }

    def create_template(self):
        self.template.add_resource(WaitConditionHandle("VPC"))


class Bastion(Blueprint):
    VARIABLES = {
        "VpcId": {"type": EC2VPCId, "description": "Vpc Id"},
        "DefaultSG": {"type": EC2SecurityGroupId,
                      "description": "Top level security group."},
        "PublicSubnets": {"type": EC2SubnetIdList,
                          "description": "Subnets to deploy public "
                                         "instances in."},
        "PrivateSubnets": {"type": EC2SubnetIdList,
                           "description": "Subnets to deploy private "
                                          "instances in."},
        "AvailabilityZones": {"type": CFNCommaDelimitedList,
                              "description": "Availability Zones to deploy "
                                             "instances in."},
        "InstanceType": {"type": CFNString,
                         "description": "EC2 Instance Type",
                         "default": "m3.medium"},
        "MinSize": {"type": CFNNumber,
                    "description": "Minimum # of instances.",
                    "default": "1"},
        "MaxSize": {"type": CFNNumber,
                    "description": "Maximum # of instances.",
                    "default": "5"},
        "SshKeyName": {"type": EC2KeyPairKeyName},
        "OfficeNetwork": {
            "type": CFNString,
            "description": "CIDR block allowed to connect to bastion hosts."},
        "ImageName": {
            "type": CFNString,
            "description": "The image name to use from the AMIMap (usually "
                           "found in the config file.)",
            "default": "bastion"},
    }

    def create_template(self):
        return


class PreOneOhBastion(Blueprint):
    """Used to ensure old blueprints won't be usable in 1.0"""
    PARAMETERS = {
        "VpcId": {"type": "AWS::EC2::VPC::Id", "description": "Vpc Id"},
        "DefaultSG": {"type": "AWS::EC2::SecurityGroup::Id",
                      "description": "Top level security group."},
        "PublicSubnets": {"type": "List<AWS::EC2::Subnet::Id>",
                          "description": "Subnets to deploy public "
                                         "instances in."},
        "PrivateSubnets": {"type": "List<AWS::EC2::Subnet::Id>",
                           "description": "Subnets to deploy private "
                                          "instances in."},
        "AvailabilityZones": {"type": "CommaDelimitedList",
                              "description": "Availability Zones to deploy "
                                             "instances in."},
        "InstanceType": {"type": "String",
                         "description": "EC2 Instance Type",
                         "default": "m3.medium"},
        "MinSize": {"type": "Number",
                    "description": "Minimum # of instances.",
                    "default": "1"},
        "MaxSize": {"type": "Number",
                    "description": "Maximum # of instances.",
                    "default": "5"},
        "SshKeyName": {"type": "AWS::EC2::KeyPair::KeyName"},
        "OfficeNetwork": {
            "type": "String",
            "description": "CIDR block allowed to connect to bastion hosts."},
        "ImageName": {
            "type": "String",
            "description": "The image name to use from the AMIMap (usually "
                           "found in the config file.)",
            "default": "bastion"},
    }

    def create_template(self):
        return
