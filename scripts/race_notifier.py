import subprocess
import requests
import json
try:
    from config import DISCORD_WEBHOOK_URL
except ImportError:
    DISCORD_WEBHOOK_URL = None

class RaceNotifier:
    """
    通知を行うクラス (Mac Desktop / Discord Webhook)
    """
    def __init__(self):
        self.notificationTitle = "競艇レース通知"
        self.notificationSound = "default"
        self.discordWebhookUrl = DISCORD_WEBHOOK_URL
    
    def sendNotification(self, message, title=None):
        """
        通知を送信する。
        Discord Webhook設定済みならDiscordへ、なければMacへ送信する。
        """
        if title is None:
            title = self.notificationTitle
            
        fullMessage = f"**[{title}]**\n{message}"
        print(f"通知試行: {title} (Method: {'Discord' if self.discordWebhookUrl else 'Mac'})")
        
        if self.discordWebhookUrl:
            return self._sendDiscord(fullMessage)
        else:
            return self._sendMac(message, title)

    def _sendDiscord(self, content):
        """Discord Webhookで送信"""
        payload = {
            "content": content
        }
        
        try:
            resp = requests.post(self.discordWebhookUrl, json=payload)
            resp.raise_for_status()
            print("  -> Discord送信成功")
            return True
        except Exception as e:
            print(f"  -> Discord送信エラー: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"     Response: {e.response.text}")
            return False

    def _sendMac(self, message, title):
        """Macデスクトップ通知で送信"""
        safeTitle = title.replace('"', '\\"')
        safeMessage = message.replace('"', '\\"')
        script = f'display notification "{safeMessage}" with title "{safeTitle}" sound name "{self.notificationSound}"'
        try:
            subprocess.run(["osascript", "-e", script], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"  -> Mac通知エラー: {e}")
            return False

if __name__ == "__main__":
    notifier = RaceNotifier()
    notifier.sendNotification("これはテスト通知です。\nレース3分前です！", "通知テスト")



