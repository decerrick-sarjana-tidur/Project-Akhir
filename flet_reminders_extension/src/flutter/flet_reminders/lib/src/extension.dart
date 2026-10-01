import 'package:flet/flet.dart';

import 'native_google_sign_in_service.dart';
import 'reminder_service.dart';

class Extension extends FletExtension {
  @override
  FletService? createService(Control control) {
    switch (control.type) {
      case "NativeGoogleSignInService":
        return NativeGoogleSignInService(control: control);
      case "VaultReminderService":
        return VaultReminderService(control: control);
      default:
        return null;
    }
  }
}
