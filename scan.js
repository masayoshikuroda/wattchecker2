'use strict';

const noble = require('@abandonware/noble');

//discovered BLE device
const discovered = (peripheral) => {
    console.log(peripheral.id + ' ' + peripheral.address + " " + peripheral.advertisement.localName);
}

//BLE scan start
const scanStart = () => {
    noble.startScanning([], false);
    noble.on('discover', discovered);
}

if(noble.state === 'poweredOn'){
    scanStart();
}else{
    noble.on('stateChange', scanStart);
}
