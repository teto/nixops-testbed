/* Copyright (c) 2016 Facebook
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of version 2 of the GNU General Public
 * License as published by the Free Software Foundation.
 */

/* see https://stackoverflow.com/questions/47895179/how-to-build-bpf-program-out-of-the-kernel-tree
 * clang -O2 -emit-llvm -c test_ebpf_tc.c -o - | llc -march=bpf -filetype=obj -o bpf.o
 * Set $dev to `make INSTALL_HDR_PATH=dest headers_install`
 * 
 * Look in https://github.com/netoptimizer/prototype-kernel/blob/master/kernel/samples/bpf/Makefile
 *
 THIS WORKED !!!
nix-shell -p llvm_4 clang
clang  -O2 -emit-llvm -c test_ebpf_tc.c -v -I${dev}/build/dest -I${dev}/build/include -I${dev}/build/arch/x86/include/uapi -I${dev}/arch/x86/include| llc -march=bpf -filetype=obj -o bpf.o
 *
 * Supported 32 bit action return codes from the C program and their meanings ( linux/pkt_cls.h ):
           TC_ACT_OK (0) , will terminate the packet processing pipeline and
           allows the packet to proceed
           TC_ACT_SHOT (2) , will terminate the packet processing pipeline
           and drops the packet
           TC_ACT_UNSPEC (-1) , will use the default action configured from
           tc (similarly as returning -1 from a classifier)
           TC_ACT_PIPE (3) , will iterate to the next action, if available
           TC_ACT_RECLASSIFY (1) , will terminate the packet processing
           pipeline and start classification from the beginning
           else , everything else is an unspecified return code<Paste>
 */

#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/if_packet.h>
#include <linux/ip.h>
#include <linux/in.h>
#include <linux/tcp.h>
#include <linux/filter.h>
#include <linux/pkt_cls.h>
#include <linux/kernel.h>

/* #include <linux/byteorder/generic.h> */
#include <asm/byteorder.h>
/* copied from samples/bpf/bpf_helpers.h */
#include "bpf_helpers.h" 


/* for offsetof */
#include <stddef.h> 



#define SEC(NAME) __attribute__((section(NAME), used))
#define PIN_GLOBAL_NS		2

struct bpf_elf_map {
	__u32 type;
	__u32 size_key;
	__u32 size_value;
	__u32 max_elem;
	__u32 flags;
	__u32 id;
	__u32 pinning;
};

/* copy of 'struct ethhdr' without __packed */
/* struct eth_hdr { */
/* 	unsigned char   h_dest[ETH_ALEN]; */
/* 	unsigned char   h_source[ETH_ALEN]; */
/* 	unsigned short  h_proto; */
/* }; */


struct bpf_elf_map SEC("maps") map = {
        .type = BPF_MAP_TYPE_ARRAY,
        .size_key = sizeof(int),
        .size_value = sizeof(__u32),
        .pinning = PIN_GLOBAL_NS,
        .max_elem = 2,
};

/* printt */
#define DEBUG 1
#ifdef  DEBUG
/* Only use this for debug output. Notice output from bpf_trace_printk()
 *  * end-up in /sys/kernel/debug/tracing/trace_pipe
 *   */
#define bpf_debug(fmt, ...)						\
			({							\
			char ____fmt[] = fmt;				\
			bpf_trace_printk(____fmt, sizeof(____fmt),	\
			##__VA_ARGS__);			\
			})
#else
#define bpf_debug(fmt, ...) { } while (0)
#endif

/* TCPHDR_FIN */
/* #define FIN 0 */
/* #define SYN 1 */
/* #define RST 2 */
/* #define PSH 3 */
/* #define ACK 4 */
/* #define URG 5 */
/* #define ECE 6 */
/* #define CWR 7 */

#define TCPHDR_FIN 0x01
#define TCPHDR_SYN 0x02
#define TCPHDR_RST 0x04
#define TCPHDR_PSH 0x08
#define TCPHDR_ACK 0x10
#define TCPHDR_URG 0x20
#define TCPHDR_ECE 0x40
#define TCPHDR_CWR 0x80

/* int get_flag(__u8 flags, int flag) { */
/* 	return flags & (1 << flag); */
/* } */

/* TCPHDR_FIN would be undeclared */
/* ETH_HLEN defined in libc */


SEC("action") int handle_ingress(struct __sk_buff *skb)
{

	/* void *data = (void *)(long)skb->data; */
	/* void *data_end = (void *)(long)skb->data_end; */
	/* struct eth_hdr *eth = data; */
	/* struct iphdr *iph = data + sizeof(*eth); */
	/* TODO rename into th */
	struct tcphdr *tcp = (struct tcphdr *) skb + (ETH_HLEN + sizeof(struct iphdr));
	int key = 0, key2 = 1;
	__u32 *seen;
	seen = bpf_map_lookup_elem(&map, &key);
	if(!seen) {
		__u32 val = 0;
		if(bpf_map_update_elem(&map, &key, &val, BPF_NOEXIST))
			return TC_ACT_OK;
	}
	seen = bpf_map_lookup_elem(&map, &key);
	if(!seen)
		return TC_ACT_OK;

	if(!tcp)
		return TC_ACT_OK;
	__u16 *addr = (__u16 *) (&(tcp -> ack_seq) + 1);
	/* tcp_flag_byte TCPHDR_PSH used with tcp_flag_word */

	/* u8 tcp_flag_byte(); Look at/taken from bcc/tools/tcpdrop.py */
	/* __u8 flags = ((u_int8_t *)tcp)[13]; */

	/* generates an error
	 * load_byte/half/word
	 * */
	/* __be32 flags = *tcp_flag_word(tcp); 
	 * load_byte　c la position dans le SKB */
	/* __u64 flags = load_byte(skb, tcp_flag_word(tcp) - skb); */
	/* __u64 flags = load_byte(skb, ((__u8 *)tcp)[13]); */
	/* __u64 flags = 0; */

	/* print("tcp %d", TCPHDR_FIN); */


/* defined in linux #define tcp_flag_word(tp) ( ((union tcp_word_hdr *)(tp))->words [3]) */ 

	/* lspcu can show you endianness	Little Endian
	 my vm is also Byte Order:          Little Endian 
	 TCP_FLAG_* are defined as bigendian
	 The load_xxx function does a bswap before returning the short/word/dword,
	so the value in register will always be host endian
	 */
	/* TCPHDR_PSH = __constant_cpu_to_be32(0x00080000), 
	TCPHDR_CWR = __constant_cpu_to_be32(0x00800000), */
	__u8 flags = load_byte(skb, ETH_HLEN + sizeof(struct iphdr) + offsetof(struct tcphdr, ack_seq) + 4 + 1);
	/* __u64 flags2 = (__u64) load_half(skb, ETH_HLEN + sizeof(struct iphdr) + offsetof(struct tcphdr, ack_seq) + 4); */
	/* __u64 flags3 = load_word(skb, ETH_HLEN + sizeof(struct iphdr) + sizeof(__be32 ) * 4); */
	/* htonl(flags) */

	/* flags2 = flags2 << 8; */
	/* /1* __u8 tcpflags; *1/ */
	/* /1* bpf_probe_read(&tcpflags, sizeof(tcpflags), &tcp_flag_byte(tcp)); *1/ */

	/* /1* bpf_debug("flag_word gives %u while flags2 gives %u\n", flags, flags); *1/ */
	/* bpf_debug("TOTO\n"); */
	/* /1* bpf_debug("%u\n", tcp->ack_seq); *1/ */
	/* bpf_debug("%x flags2 gives %x\n", TCPHDR_CWR, TCPHDR_PSH); /1* shows "8000 flags2 gives 800" *1/ */
	/* bpf_debug("%x flags2 gives %x\n", flags, flags2); */
	/* bpf_debug("%x while flags3 gives %x \n", flags, flags3); */
	/* /1* bpf_debug(">> SYN %04x vs flags << 8 %04x\n", TCPHDR_SYN, flags << 8); *1/ */

	/* bpf_debug("comparing %u flags2 gives %u and %u\n", TCPHDR_PSH & flags, TCPHDR_PSH & flags2, TCPHDR_PSH & flags3); */
	/* bpf_debug("comparing %u flags2 gives %u and %u\n", TCPHDR_PSH & flags, TCPHDR_PSH & (flags >> 8), TCPHDR_PSH & (flags >> 16)); */
	/* flags = flags << 8; */
	/* __u64 flags = (__u64) load_byte(skb, ETH_HLEN + sizeof(struct iphdr) ); */
	

	/* if( tcp->syn ) { */
	if( flags & TCPHDR_SYN) {
		__u32 val = 0;
		*seen = 0;
		bpf_debug("RESET SEEN\n");
		bpf_map_update_elem(&map, &key, &val, BPF_EXIST);
		bpf_map_update_elem(&map, &key2, &val, BPF_ANY);
	}
	// We here only handle the little endian case
        
        // fin is at the 1st position of the byte in little endian
	if (0 && (flags & TCPHDR_FIN)) { // tail drop
		bpf_debug("DROP, PSH: %x\n", flags & TCPHDR_PSH);
                bpf_debug("DROP, FIN: %x\n", flags & TCPHDR_FIN);

		return TC_ACT_SHOT;
	}
	if (!(flags & TCPHDR_SYN) && !*seen) {
		__u8 off = ((__u8) load_byte(skb, ETH_HLEN + sizeof(struct iphdr) + offsetof(struct tcphdr, ack_seq) + 4) & 0xF0) >> 4;
		int header_size = off*4;
		int packet_len = skb -> len - (ETH_HLEN + sizeof(struct iphdr) + header_size);
		//bpf_debug("HERE, LEN = %d\n", packet_len);
		if(flags & TCPHDR_PSH ) {
			bpf_debug("POTENTIALLY TAIL\n");
			// this is potentially the tail
			// check that is is the tail by analyzing the end of the packet to find the DROPME tag
			/*char tag[] = "DROPME";
			int i = 0;
			for (i = 0 ; i < 6 ; i++) {
				bpf_debug("COMPARE %c with %c\n", load_byte(skb, skb -> len - 5 + i), tag[i]);
				if ((char) load_byte(skb, skb -> len - 5 + i) != tag[i])
					return TC_ACT_OK;
			}*/
			char D = load_byte(skb, skb -> len - 7);
			char R = load_byte(skb, skb -> len - 6);
			char O = load_byte(skb, skb -> len - 5);
			char P = load_byte(skb, skb -> len - 4);
			char M = load_byte(skb, skb -> len - 3);
			char E = load_byte(skb, skb -> len - 2);
			if (!(D == 'D' && R == 'R' && O == 'O' && P == 'P' && M == 'M' && E == 'E'))
				return TC_ACT_OK;
			// we are now sure that it is the tail that we want to drop
			struct iphdr *iphdr = (struct iphdr *) skb + ETH_HLEN;
			////// LOAD IP ADDR BYTE PER BYTE
			__u32 b1 = ((__u32) load_byte(skb, ETH_HLEN + offsetof(struct iphdr, daddr)) << 24);
                        __u32 b2 = load_byte(skb, ETH_HLEN + offsetof(struct iphdr, daddr) + 1) << 16;
                        __u32 b3 = load_byte(skb, ETH_HLEN + offsetof(struct iphdr, daddr) + 2) << 8;
                        __u32 b4 = load_byte(skb, ETH_HLEN + offsetof(struct iphdr, daddr) + 3);
			////// END LOAD IP ADDR BYTE PER BYTE 
			__u32 daddr = __constant_be32_to_cpu(b1 + b2 + b3 + b4/*iphdr -> daddr*/);
			bpf_debug("TOTO\n");
			bpf_debug("TAIL DROP, %d, daddr = %x\n", packet_len, daddr);
			__u32 val = 1;
			__u32 val2 = 2;//(__u32) daddr;
			*seen = 1;
                	bpf_map_update_elem(&map, &key, &val, BPF_EXIST);
                        bpf_map_update_elem(&map, &key2, &daddr, BPF_ANY);
			return TC_ACT_SHOT;
		} else {
			//bpf_debug("LET PASS LENGTH %d, header_size = %d (%d*4)\n", packet_len, header_size, header_size/4);
		}
	}
	return TC_ACT_OK;

}

char _license[] SEC("license") = "GPL";
