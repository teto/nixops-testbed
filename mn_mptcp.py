'''
This is an extension of mininet to work with mptcp

'''

# Problem we wanna solve here:
# when the interface goes up, it should trigger the hook
# class MPTCPIntf(Intf):
#     def setIP(self, *args, **kwargs):
#         pass
#     def runHook()
#         pass
    # updateIP
    # updateAddr


# TODO add MptcpHost



# iperf2 version
# server.cmd('iperf -s -i 1 -y C > out/server_' + str(number_of_paths) + '.log &')
# client.cmd('iperf -c 10.0.0.2  -n ' + dataAmount + ' -i 1 > out/client_' + str(number_of_paths) + '.log')

# netperf version
# server.cmd('iperf -s -i 1 -y C > out/server_' + str(number_of_paths) + '.log &')
# client.cmd('iperf -c 10.0.0.2  -n ' + dataAmount + ' -i 1 > out/client_' + str(number_of_paths) + '.log')

# flent version
# flent rrul -p ping_cdf -l 60 -H address-of-netserver -t text-to-be-included-in-plot -o filename.png
# server.cmd('netserver -Ddf > out/server_' + str(number_of_paths) + '.log &')
# TODO test manually first
# client.cmd('flent rrul -p ping_cdf -l 60 -H 10.0.0.2 -t "mon titre" -o filename.png')

