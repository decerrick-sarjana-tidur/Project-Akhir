import 'package:flet/flet.dart';
import 'package:google_sign_in/google_sign_in.dart';

class NativeGoogleSignInService extends FletService {
  NativeGoogleSignInService({required super.control});

  final GoogleSignIn _googleSignIn = GoogleSignIn.instance;
  bool _initialized = false;

  @override
  void init() {
    super.init();
    control.addInvokeMethodListener(_invokeMethod);
  }

  Future<dynamic> _invokeMethod(String name, dynamic args) async {
    if (name != 'sign_in') {
      throw Exception('Unknown NativeGoogleSignInService method: $name');
    }

    if (!_initialized) {
      await _googleSignIn.initialize(
        serverClientId: args['server_client_id'] as String,
      );
      _initialized = true;
    }

    final account = await _googleSignIn.authenticate();
    final idToken = account.authentication.idToken;
    if (idToken == null || idToken.isEmpty) {
      throw StateError('Google Sign-In tidak memberikan ID token.');
    }
    return idToken;
  }

  @override
  void dispose() {
    control.removeInvokeMethodListener(_invokeMethod);
    super.dispose();
  }
}
