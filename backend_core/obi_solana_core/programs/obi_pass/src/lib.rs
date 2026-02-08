use anchor_lang::prelude::*;
use anchor_spl::token_interface::{Mint, TokenAccount, TokenInterface};
use anchor_spl::associated_token::AssociatedToken;

declare_id!("2xESoWwTmrvmjoev3ZTh52XTnMpzPLQycf7VU2e6D3sv");

#[program]
pub mod obi_pass {
    use super::*;

    // 1. Inicializar a "Casa da Moeda" (Mint Authority)
    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        msg!("🚀 OBI Pass: Protocolo Inicializado!");
        Ok(())
    }

    // 2. Comprar Licença (Mint OBI Pass)
    // O usuário paga uma taxa (1 SOL) e recebe 1 Token 2022 (SBT ou NFT)
    pub fn mint_license(ctx: Context<MintLicense>) -> Result<()> {
        msg!("🎟️ Mintando OBI Pass para: {}", ctx.accounts.buyer.key());

        // Preço da Licença: 1 SOL (Hardcoded para MVP)
        let price_lamports: u64 = 1_000_000_000;

        msg!("💰 Processando pagamento de {} lamports...", price_lamports);

        // Transferir SOL do Buyer para o Treasury
        let transfer_ix = anchor_lang::solana_program::system_instruction::transfer(
            &ctx.accounts.buyer.key(),
            &ctx.accounts.treasury.key(),
            price_lamports,
        );

        anchor_lang::solana_program::program::invoke(
            &transfer_ix,
            &[
                ctx.accounts.buyer.to_account_info(),
                ctx.accounts.treasury.to_account_info(),
                ctx.accounts.system_program.to_account_info(),
            ],
        )?;

        msg!("✅ Pagamento confirmado!");

        // Mintar 1 Token para o comprador
        // Usando Token Extensions (Token 2022) para metadados on-chain
        anchor_spl::token_interface::mint_to(
            CpiContext::new_with_signer(
                ctx.accounts.token_program.to_account_info(),
                anchor_spl::token_interface::MintTo {
                    mint: ctx.accounts.mint.to_account_info(),
                    to: ctx.accounts.buyer_token_account.to_account_info(),
                    authority: ctx.accounts.mint_authority.to_account_info(),
                },
                &[], // Seeds para PDA se necessário: idealmente seeds=[b"authority", bump]
            ),
            1, // Quantidade: 1 Licença
        )?;

        msg!("✅ Licença emitida com sucesso!");
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,
    
    #[account(
        init,
        payer = payer,
        mint::decimals = 0,
        mint::authority = mint_authority,
        mint::freeze_authority = mint_authority,
    )]
    pub mint: InterfaceAccount<'info, Mint>, // Token 2022 Mint
    
    /// CHECK: PDA Authority
    #[account(seeds = [b"authority"], bump)]
    pub mint_authority: UncheckedAccount<'info>,
    
    pub system_program: Program<'info, System>,
    pub token_program: Interface<'info, TokenInterface>, // Token 2022
}

#[derive(Accounts)]
pub struct MintLicense<'info> {
    #[account(mut)]
    pub buyer: Signer<'info>,
    
    /// CHECK: Treasury Wallet que receberá o pagamento (Validar pubkey no client ou aqui)
    #[account(mut)]
    pub treasury: UncheckedAccount<'info>,

    #[account(mut)]
    pub mint: InterfaceAccount<'info, Mint>,
    
    /// CHECK: PDA Authority que assina o mint
    #[account(seeds = [b"authority"], bump)]
    pub mint_authority: UncheckedAccount<'info>,
    
    #[account(
        init_if_needed,
        payer = buyer,
        associated_token::mint = mint,
        associated_token::authority = buyer,
    )]
    pub buyer_token_account: InterfaceAccount<'info, TokenAccount>,
    
    pub system_program: Program<'info, System>,
    pub token_program: Interface<'info, TokenInterface>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub rent: Sysvar<'info, Rent>,
}
