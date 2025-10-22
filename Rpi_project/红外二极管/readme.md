 pip install lirc
2. pip install lr-keytable    
3. sudo nano /boot/config.txt    
   dtoverlay=gpio-ir,gpio_pin=17 //更改GPIO17为红外接受口
4. dmesg | grep -i rc //搜索rc口，
5. 运行ir-keytable    //发现rc名称，并查看支持协议
6. 运行 sudo ir-keytable -s rc2 -p all //rc2为实际的rc口，将其他协议添加为支持
7. 运行 ir-keytable -s rc2 -t  //测试运行红外遥控器
