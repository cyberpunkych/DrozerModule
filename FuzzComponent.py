#!/usr/bin/env python      
# -*- coding: gbk -*-
from drozer.modules import Module, common
from drozer import android
import time

__author__ = 'zhouliwei'

"""
function: ���ڶ�Android������е��ã����Ϳ�action��������Activity
          ��Ҫ���Activity��service��broadcastReceiver
date:2017/7/14

"""


class Fuzz(Module, common.Filters, common.PackageManager, common.Provider, common.TableFormatter, common.Strings,
           common.ZipFile, common.FileSystem, common.IntentFilter):
    name = "fuzz component"
    description = "fuzz Activity, service, broadcastReceiver"
    examples = ""
    author = "zlw (zlw@xdja.com)"
    date = "2017-7-14"
    license = "BSD (3-clause)"
    path = ["xdja", "safe"]

    execute_interval = 10

    actions = ['android.intent.action.MAIN',
               'android.intent.action.VIEW',
               'android.intent.action.ATTACH_DATA',
               'android.intent.action.EDIT',
               'android.intent.action.PICK',
               'android.intent.action.CHOOSER',
               'android.intent.action.GET_CONTENT',
               'android.intent.action.DIAL',
               'android.intent.action.CALL',
               'android.intent.action.SEND',
               'android.intent.action.SENDTO',
               'android.intent.action.ANSWER',
               'android.intent.action.INSERT',
               'android.intent.action.DELETE',
               'android.intent.action.RUN',
               'android.intent.action.SYNC',
               'android.intent.action.PICK_ACTIVITY',
               'android.intent.action.SEARCH',
               'android.intent.action.WEB_SEARCH',
               'android.intent.action.FACTORY_TEST',
               'android.intent.action.TIME_TICK',
               'android.intent.action.TIME_CHANGED',
               'android.intent.action.TIMEZONE_CHANGED',
               'android.intent.action.BOOT_COMPLETED',
               'android.intent.action.PACKAGE_ADDED',
               'android.intent.action.PACKAGE_CHANGED',
               'android.intent.action.PACKAGE_REMOVED',
               'android.intent.action.PACKAGE_RESTARTED',
               'android.intent.action.PACKAGE_DATA_CLEARED',
               'android.intent.action.UID_REMOVED',
               'android.intent.action.BATTERY_CHANGED',
               'android.intent.action.ACTION_POWER_CONNECTED',
               'android.intent.action.ACTION_POWER_DISCONNECTED',
               'android.intent.action.ACTION_SHUTDOWN',
               'android.net.conn.CONNECTIVITY_CHANGE']  # Last 3 are the exception to the rule

    def add_arguments(self, parser):
        android.Intent.addArgumentsTo(parser)
        parser.add_argument("-p", "--package", default=None, help="The Package Name")

    """
      the Function to execute
    """

    def execute(self, arguments):
        # ���ж��Ƿ�������package
        if arguments.package is None:
            self.stdout.write("��ͨ��-pָ�����԰�������\n\n")
        else:
            package = self.packageManager().getPackageInfo(arguments.package,
                                                           common.PackageManager.GET_ACTIVITIES | common.PackageManager.GET_RECEIVERS | common.PackageManager.GET_PROVIDERS | common.PackageManager.GET_SERVICES)
            # �ȶ�provider���д�����Ϊһ��provider�Ƚ���
            self.__handle_providers(arguments, package)

            # ��Activity���д���
            self.__handle_activity(arguments, package)

            # ��service���д���
            self.__handle_service(arguments, package)

            # ��broadcastReceiver���д���
            self.__handle_receivers(arguments, package)

    """
        ��broadReceiver���д���
    """

    def __handle_receivers(self, arguments, package):
        self.stdout.write("===================��ʼ����broadcastReceiver===================== \n\n")
        exported_receivers = self.match_filter(package.receivers, 'exported', True)
        if len(exported_receivers) > 0:
            self.stdout.write("  %d broadcast receivers exported\n " % len(exported_receivers))

            # ����broadcast Receivers
            for receivers in exported_receivers:
                self.stdout.write(" ����ContentProvider %s \n" % receivers.name)
                # ���Ϳ� action��receiver
                self.__start_receivers(package, receivers.name)
                # ��������֮����һ��ʱ��
                time.sleep(self.execute_interval)
                # ���Ͳ���Extras��receiver
                self.__start_receivers_with_action(package, receivers.name, receivers)
                time.sleep(self.execute_interval)

        else:
            self.stdout.write(" No exported BroadcastReceiver .\n\n")
        self.stdout.write("===================��������broadcastReceiver===================== \n\n")

    """
        ����broadCastReceiver��ʹ��component������
        no action    no extras
    """

    def __start_receivers(self, package, receiver_name):
        intent = self.new("android.content.Intent")
        comp = (package.packageName, receiver_name)
        com = self.new("android.content.ComponentName", *comp)
        intent.setComponent(com)
        self.getContext().sendBroadcast(intent)

    """
        ���ʹ�action��receiver
    """

    def __start_receivers_with_action(self, package, receiver_name, receiver):
        intent = self.new("android.content.Intent")
        comp = (package.packageName, receiver_name)
        com = self.new("android.content.ComponentName", *comp)
        intent.setComponent(com)
        # ��ȡaction
        intent_filters = self.find_intent_filters(receiver, 'receiver')
        for intent_filter in intent_filters:
            if len(intent_filter.actions) > 0:
                self.stdout.write("%s  has Actions:\n" % receiver_name)
                for action in intent_filter.actions:
                    try:
                        # ��ϵͳ��action���˵�
                        if self.actions.index(action) > 0:
                            continue
                    except ValueError:
                        # ���������˵�����Զ����action����������
                        try:
                            intent.setAction(action)
                            self.getContext().sendBroadcast(intent)
                            break
                        except Exception:
                            continue

    """
       ��service���д���
    """

    def __handle_service(self, arguments, package):
        self.stdout.write("===================��ʼ����service===================== \n\n")
        exported_services = self.match_filter(package.services, 'exported', True)
        if len(exported_services) > 0:
            self.stdout.write("  %d services exported\n " % len(exported_services))

            # ����Service
            for service in exported_services:
                self.stdout.write(" ����exported service %s \n" % service.name)
                self.__start_service(service.name, arguments, package)
                time.sleep(self.execute_interval)

        else:
            self.stdout.write(" No exported services.\n\n")

        self.stdout.write("===================��ɲ���Service===================== \n\n")

    """
        ����service��Ĭ��ֻ��ȥ����service�������ݲ���,ʹ��component������
    """

    def __start_service(self, service_name, arguments, package):
        intent = self.new("android.content.Intent")
        comp = (package.packageName, service_name)
        com = self.new("android.content.ComponentName", *comp)
        intent.setComponent(com)
        self.getContext().startService(intent)

    """
        ���apk���Ƿ��е�����Activity
    """

    def __handle_activity(self, arguments, package):
        self.stdout.write("===================��ʼ����Activity===================== \n\n")
        exported_activitys = self.match_filter(package.activities, 'exported', True)
        if len(exported_activitys) > 0:
            self.stdout.write("  %d activities exported\n" % len(exported_activitys))

            # ִ��Activity����
            for activity in exported_activitys:
                self.stdout.write("����exported activity %s \n" % activity.name)
                self.__start_activity(arguments, package, activity.name)
                # ��ͣ10s��ִ����һ��
                time.sleep(self.execute_interval)
        else:
            self.stdout.write(" No exported activity.\n\n")

        self.stdout.write("===================��������Activity===================== \n\n")

    """
        ����Activity
    """

    def __start_activity(self, arguments, package, activity_name):
        try:
            intent = self.new("android.content.Intent")
            comp = (package.packageName, activity_name)
            com = self.new("android.content.ComponentName", *comp)
            intent.setComponent(com)
            intent.setFlags(0x10000000)
            self.getContext().startActivity(intent)
        except Exception:
            self.stderr.write("%s need some premission or other failure. \n " % activity_name)

    """
          ��ȡ���е�����providers
          Ȼ���ȡ
    """

    def __handle_providers(self, arguments, package):
        self.stdout.write("===================��ʼ����Contentprovider===================== \n\n")
        exported_providers = self.match_filter(package.providers, 'exported', True)
        if len(exported_providers) > 0:
            self.stdout.write("  %d content providers exported\n" % len(exported_providers))
            # ȥ��ȡ���Բ�ѯ��uri
            for provider in exported_providers:
                self.stdout.write(" ��ʼ��ѯ exported provider %s \n " % provider.name)
                self.__get_read_URi(arguments, package)
        else:
            self.stdout.write(" No exported providers.\n\n")
        self.stdout.write("===================��������Contentprovider===================== \n\n")

    """
        ��ȡ���п��Է��ʵ�ContentProvider��uri
    """

    def __get_read_URi(self, arguments, package):
        # attempt to query each content uri
        for uri in self.findAllContentUris(arguments.package):
            try:
                self.stdout.write("��ʼ��ѯ exported provider %s \n " % uri)
                response = self.contentResolver().query(uri)
                time.sleep(self.execute_interval)
            except Exception:
                response = None

            if response is None:
                self.stdout.write("Unable to Query  %s\n" % uri)
            else:
                self.stdout.write("Able to Query    %s\n" % uri)
                # ֱ��ȥ��ѯ����
                self.stdout.write("��ʼ��ѯ uri %s ��Ӧ������ \n" % uri)
                self.__read_data_from_uri(uri)

    """
        ���uri�ǿ��Զ�ȡ�ģ���ô�ʹ�uri���Զ�ȡ���ݣ��������ݴ�ӡ������
    """

    def __read_data_from_uri(self, uri):
        c = self.contentResolver().query(uri, None, None, None, None)

        if c is not None:
            rows = self.getResultSet(c)
            # ��ӡ������
            self.print_table(rows, show_headers=True, vertical=False)
        else:
            self.stdout.write("Unknown Error.\n\n")

    """
        ��ȡ���е�����Activity
    """

    def __get_activities(self, arguments, package):
        exported_activities = self.match_filter(package.activities, 'exported', True)
        if len(exported_activities) > 0:
            return exported_activities
        else:
            self.stdout.write(" No exported activities.\n\n")

    """
        ��ȡ���е�����services
    """

    def __get_services(self, arguments, package):
        exported_services = self.match_filter(package.services, "exported", True)
        if len(exported_services) > 0:
            return exported_services
        else:
            self.stdout.write(" No exported services.\n\n")

    """
        ��ȡ���е����Ĺ㲥
    """

    def __get_receivers(self, arguments, package):
        exported_receivers = self.match_filter(package.receivers, 'exported', True)
        if len(exported_receivers) > 0:
            return exported_receivers
        else:
            self.stdout.write(" No exported receivers.\n\n")
