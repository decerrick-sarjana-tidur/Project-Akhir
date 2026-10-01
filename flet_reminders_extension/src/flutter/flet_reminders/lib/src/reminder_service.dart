import 'package:flet/flet.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_timezone/flutter_timezone.dart';
import 'package:timezone/data/latest_all.dart' as tz_data;
import 'package:timezone/timezone.dart' as tz;

class VaultReminderService extends FletService {
  VaultReminderService({required super.control});

  final FlutterLocalNotificationsPlugin _notifications =
      FlutterLocalNotificationsPlugin();
  late final Future<void> _ready = _initialize();

  Future<void> _initialize() async {
    tz_data.initializeTimeZones();
    await _notifications.initialize(
      settings: const InitializationSettings(
        android: AndroidInitializationSettings('@mipmap/ic_launcher'),
        iOS: DarwinInitializationSettings(
          requestAlertPermission: false,
          requestBadgePermission: false,
          requestSoundPermission: false,
        ),
      ),
    );
  }

  @override
  void init() {
    super.init();
    control.addInvokeMethodListener(_invokeMethod);
  }

  Future<dynamic> _invokeMethod(String name, dynamic args) async {
    await _ready;
    switch (name) {
      case 'request_permission':
        final android = await _notifications
            .resolvePlatformSpecificImplementation<
                AndroidFlutterLocalNotificationsPlugin>()
            ?.requestNotificationsPermission();
        final ios = await _notifications
            .resolvePlatformSpecificImplementation<
                IOSFlutterLocalNotificationsPlugin>()
            ?.requestPermissions(alert: true, sound: true, badge: false);
        return android ?? ios ?? true;
      case 'schedule_daily':
        await _scheduleDaily(args);
        return null;
      case 'show':
        await _notifications.show(
          id: args['id'] as int,
          title: args['title'] as String,
          body: args['body'] as String,
          notificationDetails: _details,
        );
        return null;
      case 'cancel':
        await _notifications.cancel(id: args['id'] as int);
        return null;
      default:
        throw Exception('Unknown VaultReminderService method: $name');
    }
  }

  Future<void> _scheduleDaily(Map args) async {
    final timezone = await FlutterTimezone.getLocalTimezone();
    tz.setLocalLocation(tz.getLocation(timezone.identifier));
    final now = tz.TZDateTime.now(tz.local);
    var scheduled = tz.TZDateTime(
      tz.local,
      now.year,
      now.month,
      now.day,
      args['hour'] as int,
      args['minute'] as int,
    );
    if (!scheduled.isAfter(now)) {
      scheduled = scheduled.add(const Duration(days: 1));
    }

    await _notifications.zonedSchedule(
      id: args['id'] as int,
      title: args['title'] as String,
      body: args['body'] as String,
      scheduledDate: scheduled,
      notificationDetails: _details,
      androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
      matchDateTimeComponents: DateTimeComponents.time,
    );
  }

  NotificationDetails get _details => const NotificationDetails(
        android: AndroidNotificationDetails(
          'myvault_reminders',
          'Pengingat MyVault',
          channelDescription: 'Pengingat jadwal menabung MyVault',
          importance: Importance.defaultImportance,
          priority: Priority.defaultPriority,
        ),
        iOS: DarwinNotificationDetails(),
      );

  @override
  void dispose() {
    control.removeInvokeMethodListener(_invokeMethod);
    super.dispose();
  }
}