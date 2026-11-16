import uuid
import flet as ft
import paho.mqtt.client as mqtt
import json
import asyncio

BROKER = "broker.emqx.io"
PORT = 1883
TOPIC = "esp/sensorgas"
MAX_LOG = 50
MAX_PPM = 20
TOPIC_OPSI = "esp/opsi"
JENIS_GAS = ["CO", "Alcohol", "Udara", "Tolueno", "NH4", "Aceton"]


def ppm_color(ppm_value):
    try:
        v = float(ppm_value)
    except (ValueError, TypeError):
        return ft.Colors.GREY
    if v < 12:
        return ft.Colors.GREEN
    elif v <= 18:
        return ft.Colors.ORANGE
    return ft.Colors.RED


async def main(page: ft.Page):
    page.title = "Gas Sensor"
    page.theme_mode = ft.ThemeMode.DARK 
    page.padding = 20                   

    title = ft.Text(size=16, color=ft.Colors.WHITE_70)                   
    status = ft.Text(size=20, weight=ft.FontWeight.BOLD)                
    ppm = ft.Text("0", size=36, weight=ft.FontWeight.BOLD,font_family="Consolas")                      
    connected = ft.Text("Connecting...", color=ft.Colors.ORANGE)
    value = ft.Text("Waiting for data...", size=40, font_family="Consolas")
    log = ft.ListView(expand=True, spacing=4, auto_scroll=True)
    determinate_ring = ft.ProgressRing(width=150, height=150, stroke_width=12, value=0, color=ft.Colors.GREEN, bgcolor=ft.Colors.WHITE_12)
    sent_info = ft.Text("", size=12, color=ft.Colors.WHITE_54)

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"flet-{uuid.uuid4().hex[:8]}",
    )


# DISPLAY DATA
    def ppm_display(msg):
        data = json.loads(msg)
        ppm_data = data['ppm']
        ppm.value = str(ppm_data)
        color = ppm_color(ppm_data)  
        ppm.color = color

        try:
            determinate_ring.value = min(ppm_data / MAX_PPM, 1.0)
            determinate_ring.color = color   
            determinate_ring.update()
        except(ValueError, TypeError) as e:
            print("Ring error:", e)

        ppm.update()

    def status_display(msg):
        data = json.loads(msg)
        status_data = data['status']

        formated_text = f"Status: {status_data}"

        status.value = formated_text
        status.color = ppm_color(data['ppm']) 
        status.update()


    def title_display(msg):
        data = json.loads(msg)
        device_name = data['device']
        gas_type = data['gas']

        formated_text = f"Device: {device_name} \nGas: {gas_type}"

        title.value = formated_text
        title.update()

    def control_update(msg):
        title_display(msg)
        ppm_display(msg)
        status_display(msg)

        value.value = msg
        log.controls.append(ft.Text(msg))

        if len(log.controls) > MAX_LOG:
            del log.controls[:-MAX_LOG]

        page.update()


#   MQTT SETUP
    def on_connect(client, userdata, flags, reason_code, properties):
        if(reason_code == 0):
            client.subscribe(TOPIC)
            connected.value, connected.color = "Connected", ft.Colors.GREEN
        else:
            connected.value, connected.color = f"Failed to connect, return code{reason_code}", ft.Colors.RED
        page.update()

    def on_disconnect(client, userdata, flags, reason_code, properties):
        connected.value, connected.color = "Disconnected", ft.Colors.RED
        page.update()

    def on_message(client, userdata, msg):
        payload = msg.payload.decode("utf-8", errors="replace")
        print("Received:", payload)
        page.pubsub.send_all(payload)


    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    def cleanup(e):
        client.loop_stop()
        client.disconnect()

    page.on_disconnect = cleanup


    def make_publish(index):
        def handler(e):
            client.publish(TOPIC_OPSI, str(index))
            sent_info.value = f"Sent {index} ({JENIS_GAS[index]}) to {TOPIC_OPSI}"
            sent_info.update()
        return handler

    gas_buttons = ft.Row(
        [ft.Button(name, on_click=make_publish(i)) for i, name in enumerate(JENIS_GAS)],
        wrap=True,
        spacing=10,
        run_spacing=10,
    )


    page.add(
        ft.Row([ft.Text("Gas Sensor", size=24, weight=ft.FontWeight.BOLD), connected],
               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Container(
            title,
            padding=15,
            border_radius=12,
            bgcolor=ft.Colors.WHITE_10,
        ),
        ft.Divider(),
        ft.Text("History"),
        ft.Container(
            ft.Row(
                [
                    ft.Stack(
                        [
                            determinate_ring,
                            ft.Container(ppm, width=150, height=150,
                             alignment=ft.Alignment(0, 0)),
                        ],
                        width=150,
                        height=150,
                    ),
                    ft.Column(
                        [status, ft.Text("ppm", size=14, color=ft.Colors.WHITE_54)],
                        spacing=4,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
            ),
            padding=20,
            border_radius=16,
            bgcolor=ft.Colors.WHITE_10,
        ),
        ft.Text("Select Gas"),
        ft.Container(
            ft.Column([gas_buttons, sent_info]),
            padding=15,
            border_radius=12,
            bgcolor=ft.Colors.WHITE_10,
        ),
        # ft.Container(log, expand=True),
    )

    page.pubsub.subscribe(control_update)
    client.connect_async(BROKER, PORT, keepalive=60)
    client.loop_start()



if __name__ == "__main__":
    ft.run(main)