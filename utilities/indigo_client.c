#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <indigo/indigo_bus.h>
#include <indigo/indigo_client.h>

#define MOUNT_NAME "Mount Simulator @ indigosky"

static indigo_client client;

static bool connected = false;

static indigo_result client_attach(indigo_client *client) {
  indigo_log("Client attached to INDIGO bus...");
  indigo_enumerate_properties(client, &INDIGO_ALL_PROPERTIES);
  return INDIGO_OK;
}

static indigo_result client_define_property(indigo_client *client, indigo_device *device, indigo_property *property, const char *message) {
  if (!strcmp(property->device, MOUNT_NAME) && !strcmp(property->name, CONNECTION_PROPERTY_NAME)) {
    if (!indigo_get_switch(property, CONNECTION_CONNECTED_ITEM_NAME)) {
      indigo_device_connect(client, MOUNT_NAME);
    } else {
      connected = true;
    }
  }
  return INDIGO_OK;
}

static indigo_result client_update_property(indigo_client *client, indigo_device *device, indigo_property *property, const char *message) {
  if (!strcmp(property->device, MOUNT_NAME) && !strcmp(property->name, CONNECTION_PROPERTY_NAME)) {
    if (indigo_get_switch(property, CONNECTION_CONNECTED_ITEM_NAME)) {
      connected = true;
      indigo_log("Mount connected.");
    }
  }
  return INDIGO_OK;
}

static indigo_result client_detach(indigo_client *client) {
  indigo_log("Client detached.");
  return INDIGO_OK;
}

static void send_mount_slew(double ra, double dec) {
  const char *items[] = { MOUNT_RA_ITEM_NAME, MOUNT_DEC_ITEM_NAME };
  double values[] = { ra, dec };
  indigo_change_number_property(&client, MOUNT_NAME, MOUNT_EQUATORIAL_COORDINATES_PROPERTY_NAME, 2, items, values);
}

static void process_command(const char *line) {
  if (strncmp(line, "mount_slew", 10) == 0) {
    double ra = 0.0, dec = 0.0;
    sscanf(line, "mount_slew RA=%lf DEC=%lf", &ra, &dec);
    send_mount_slew(ra, dec);
    printf("slewing mount to RA=%.2f DEC=%.2f\n", ra, dec);
    fflush(stdout);
  } else if (strncmp(line, "exit", 4) == 0) {
    printf("shutting down\n");
    fflush(stdout);
    indigo_device_disconnect(&client, MOUNT_NAME);
    indigo_detach_client(&client);
    indigo_stop();
    exit(0);
  } else {
    printf("unknown command: %s\n", line);
    fflush(stdout);
  }
}

int main(int argc, const char *argv[]) {
  indigo_main_argc = argc;
  indigo_main_argv = argv;
  indigo_set_log_level(INDIGO_LOG_INFO);
  indigo_start();

  static indigo_client client_template = {
    "MountClient", false, NULL, INDIGO_OK, INDIGO_VERSION_CURRENT, NULL,
    client_attach,
    client_define_property,
    client_update_property,
    NULL,
    NULL,
    client_detach
  };
  client = client_template;

  indigo_attach_client(&client);

  indigo_server_entry *server;
  indigo_connect_server("indigosky", "indigosky.local", 7624, &server);

  // stdin command loop
  char line[1024];
  while (fgets(line, sizeof(line), stdin)) {
    process_command(line);
  }

  return 0;
}